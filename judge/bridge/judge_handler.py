import hmac
import json
import logging
import threading
import time
from collections import deque, namedtuple
from operator import itemgetter

from django import db
from django.conf import settings
from django.utils import timezone

# from judge import event_poster as event
from judge.bridge.base_handler import ZlibPacketHandler, proxy_list
# from judge.caching import finished_submission
# from judge.models import Judge, Language, LanguageLimit, Problem, RuntimeVersion, Submission, SubmissionTestCase
from judge.models import Judge, Language, Submission, Task, TaskData

logger = logging.getLogger('judge.bridge')
json_log = logging.getLogger('judge.json.bridge')


class JudgeHandler(ZlibPacketHandler):
    proxies = proxy_list(settings.BRIDGED_JUDGE_PROXIES or [])

    def __init__(self, request, client_address, server, judges):
        super().__init__(request, client_address, server)

        self.judges = judges  # JudgeList
        self.handlers = {
            'grading-begin': self.on_grading_begin,
            'grading-end': self.on_grading_end,
            'compile-error': self.on_compile_error,
            'compile-message': self.on_compile_message,
            'batch-begin': self.on_batch_begin,
            'batch-end': self.on_batch_end,
            'test-case-status': self.on_test_case,
            'internal-error': self.on_internal_error,
            'submission-terminated': self.on_submission_terminated,
            'submission-acknowledged': self.on_submission_acknowledged,
            'ping-response': self.on_ping_response,
            'supported-problems': self.on_supported_problems,
            'handshake': self.on_handshake,
        }
        self.name = None
        self.judge_address = None
        self.judge = None  # Judge object from models
        self._working = False
        self.executors = {}  # A dictionary that contains languages and their respective information
        self.tasks = {}
        self._tasks = []
        self.batch_id = None  # current batch id
        self.in_batch = False  # self-explanation
        # dummy thread
        self._stop_ping = threading.Event()
        self._non_scaled_points = None
        self._non_scaled_total = None

    # Acts like a property. Returns True if the corresponding judge is working.
    @property
    def working(self):
        return bool(self._working)

    def _make_json_log(self, packet=None, sub=None, **kwargs):
        data = {
            'judge': self.name,
            'address': self.judge_address,
        }
        if sub is None and packet is not None:
            sub = packet.get('submission-id')
        if sub is not None:
            data['submission'] = sub
        data.update(kwargs)
        return json.dumps(data)

    def _packet_exception(self):
        json_log.exception(self._make_json_log(sub=self._working, info='packet processing exception'))

    def on_malformed(self, packet):
        logger.error('%s: Malformed packet: %s', self.name, packet)
        json_log.exception(self._make_json_log(sub=self._working, info='malformed json packet'))

    def on_packet(self, data):
        logger.debug(f"Packet: {data}")
        try:
            try:
                data = json.loads(data)
                if 'name' not in data:
                    raise ValueError
            except ValueError:
                self.on_malformed(data)
            else:
                handler = self.handlers.get(data['name'], self.on_malformed)
                handler(data)
        except Exception:
            logger.exception('Error in packet handling (Judge-side): %s', self.name)
            self._packet_exception()
            # You can't crash here because you aren't so sure about the judges
            # not being malicious or simply malformed. THIS IS A SERVER!

    # send data to client
    def send(self, data):
        super().send(json.dumps(data, separators=(',', ':')))

    def _authenticate(self, id, key):
        try:
            judge = Judge.objects.get(name=id)
        except Judge.DoesNotExist:
            return False

        if not hmac.compare_digest(judge.auth_key, key):
            logger.warning('Judge authentication failure: %s', self.client_address)
            json_log.warning(self._make_json_log(action='auth', judge=id, info='judge failed authentication'))
            return False

        if judge.is_blocked:
            json_log.warning(self._make_json_log(action='auth', judge=id, info='judge authenticated but is blocked'))
            return False

        return True

    def ping(self):
        self.send({'name': 'ping', 'when': time.time()})

    def _ping_thread(self):
        try:
            while True:
                self.ping()
                if self._stop_ping.wait(10):
                    break
        except Exception:
            logger.exception('Ping error in %s', self.name)
            self.close()
            raise

    def _connected(self):
        judge = self.judge = Judge.objects.get(name=self.name)
        judge.start_time = timezone.now()
        judge.online = True
        judge.tasks.set(TaskData.objects.filter(judge_code__in=list(self.tasks.keys())))
        judge.runtimes.set(Language.objects.filter(key__in=list(self.executors.keys())))

        # Delete now in case we somehow crashed and left some over from the last connection
        # RuntimeVersion.objects.filter(judge=judge).delete()
        # versions = []
        # for lang in judge.runtimes.all():
        #     versions += [
        #         RuntimeVersion(language=lang, name=name, version='.'.join(map(str, version)), priority=idx, judge=judge)
        #         for idx, (name, version) in enumerate(self.executors[lang.key])
        #     ]
        # RuntimeVersion.objects.bulk_create(versions)
        judge.last_ip = self.client_address[0]
        judge.save()
        self.judge_address = '[%s]:%s' % (self.client_address[0], self.client_address[1])
        json_log.info(self._make_json_log(action='auth', info='judge successfully authenticated',
                                          executors=list(self.executors.keys())))

    def on_handshake(self, packet):
        if 'id' not in packet or 'key' not in packet:
            logger.warning('Malformed handshake: %s', self.client_address)
            self.close()
            return

        if not self._authenticate(packet['id'], packet['key']):
            self.close()
            return

        self.timeout = 60
        self._tasks = packet['problems']
        self.tasks = dict(self._tasks)
        self.executors = packet['executors']
        self.name = packet['id']

        self.send({'name': 'handshake-success'})
        logger.info('Judge authenticated: %s (%s)', self.client_address, packet['id'])
        self.judges.register(self)
        threading.Thread(target=self._ping_thread).start()
        self._connected()

    def on_connect(self):
        self.timeout = 15
        logger.info('Judge connected from: %s', self.client_address)
        json_log.info(self._make_json_log(action='connect'))

    def on_grading_begin(self, packet):
        logger.info('%s: Grading has begun on: %s', self.name, packet['submission-id'])
        if Submission.objects.filter(id=packet['submission-id']).update(
                status='G'):
            # SubmissionTestCase.objects.filter(submission_id=packet['submission-id']).delete()
            # event.post('sub_%s' % Submission.get_id_secret(packet['submission-id']), {'type': 'grading-begin'})
            # self._post_update_submission(packet['submission-id'], 'grading-begin')
            json_log.info(self._make_json_log(packet, action='grading-begin'))
        else:
            logger.warning('Unknown submission: %s', packet['submission-id'])
            json_log.error(self._make_json_log(packet, action='grading-begin', info='unknown submission'))

    def _free_self(self, packet):
        self.judges.on_judge_free(self, packet['submission-id'])

    def on_grading_end(self, packet):
        logger.info('%s: Grading has ended on: %s', self.name, packet['submission-id'])
        self._free_self(packet)
        # self.batch_id = None
        #
        try:
            submission = Submission.objects.get(id=packet['submission-id'])
        except Submission.DoesNotExist:
            logger.warning('Unknown submission: %s', packet['submission-id'])
            json_log.error(self._make_json_log(packet, action='grading-end', info='unknown submission'))
            return
        #
        # time = 0
        # memory = 0
        # points = 0.0
        # total = 0
        # status = 0
        status_codes = ['SC', 'AC', 'WA', 'MLE', 'TLE', 'IR', 'RTE', 'OLE']
        # batches = {}  # batch number: (points, total)
        #
        # for case in SubmissionTestCase.objects.filter(submission=submission):
        #     time += case.time
        #     if not case.batch:
        #         points += case.points
        #         total += case.total
        #     else:
        #         if case.batch in batches:
        #             batches[case.batch][0] = min(batches[case.batch][0], case.points)
        #             batches[case.batch][1] = max(batches[case.batch][1], case.total)
        #         else:
        #             batches[case.batch] = [case.points, case.total]
        #     memory = max(memory, case.memory)
        #     i = status_codes.index(case.status)
        #     if i > status:
        #         status = i
        #
        # for i in batches:
        #     points += batches[i][0]
        #     total += batches[i][1]
        #
        # points = round(points, 1)
        # total = round(total, 1)
        # submission.case_points = points
        # submission.case_total = total
        #
        # problem = submission.problem
        # sub_points = round(points / total * problem.points if total > 0 else 0, 3)
        # if not problem.partial and sub_points != problem.points:
        #     sub_points = 0
        #
        submission.status = 'D'
        # submission.time = time
        # submission.memory = memory
        # submission.points = sub_points
        submission.points = submission.task.points * (
            submission.non_scaled_points / submission.non_scaled_total if submission.non_scaled_total != 0 else 1
        )  # scale points
        # submission.result = status_codes[status]
        submission.result = status_codes[submission.internal_result]
        submission.save()
        #
        # json_log.info(self._make_json_log(
        #     packet, action='grading-end', time=time, memory=memory,
        #     points=sub_points, total=problem.points, result=submission.result,
        #     case_points=points, case_total=total, user=submission.user_id,
        #     problem=problem.code, finish=True,
        # ))
        #
        # if problem.is_public and not problem.is_organization_private:
        #     submission.user._updating_stats_only = True
        #     submission.user.calculate_points()
        #
        # problem._updating_stats_only = True
        # problem.update_stats()
        # submission.update_contest()
        #
        # finished_submission(submission)
        #
        # event.post('sub_%s' % submission.id_secret, {
        #     'type': 'grading-end',
        #     'time': time,
        #     'memory': memory,
        #     'points': float(points),
        #     'total': float(problem.points),
        #     'result': submission.result,
        # })
        # if hasattr(submission, 'contest'):
        #     participation = submission.contest.participation
        #     event.post('contest_%d' % participation.contest_id, {'type': 'update'})
        # self._post_update_submission(submission.id, 'grading-end', done=True)

    def on_compile_error(self, packet):
        logger.info('%s: Submission failed to compile: %s', self.name, packet['submission-id'])
        self._free_self(packet)

        if Submission.objects.filter(id=packet['submission-id']).update(status='CE', result='CE', error=packet['log']):
            # event.post('sub_%s' % Submission.get_id_secret(packet['submission-id']), {
            #     'type': 'compile-error',
            #     'log': packet['log'],
            # })
            # self._post_update_submission(packet['submission-id'], 'compile-error', done=True)
            # json_log.info(self._make_json_log(packet, action='compile-error', log=packet['log'],
            #                                   finish=True, result='CE'))
            pass
        else:
            logger.warning('Unknown submission: %s', packet['submission-id'])
            json_log.error(self._make_json_log(packet, action='compile-error', info='unknown submission',
                                               log=packet['log'], finish=True, result='CE'))

    def on_compile_message(self, packet):
        pass

    def on_batch_begin(self, packet):
        logger.info('%s: Batch began on: %s', self.name, packet['submission-id'])
        self.in_batch = True
        if self.batch_id is None:
            self.batch_id = 0
        self.batch_id += 1

        json_log.info(self._make_json_log(packet, action='batch-begin', batch=self.batch_id))

    def on_batch_end(self, packet):
        self.in_batch = False
        id = packet['submission-id']
        try:
            submission = Submission.objects.get(id=id)
            if self._non_scaled_points is not None:
                submission.non_scaled_points += self._non_scaled_points
            if self._non_scaled_total is not None:
                submission.non_scaled_total += self._non_scaled_total
            submission.save()
        except Submission.DoesNotExist:
            logger.warning('Unknown submission: %s', id)
            json_log.error(self._make_json_log(packet, action='test-case', info='unknown submission'))
            return
        self._non_scaled_points = None
        self._non_scaled_total = None
        logger.info('%s: Batch ended on: %s', self.name, packet['submission-id'])
        json_log.info(self._make_json_log(packet, action='batch-end', batch=self.batch_id))

    def on_test_case(self, packet):
        logger.info('%s: %d test case(s) completed on: %s', self.name, len(packet['cases']), packet['submission-id'])

        id = packet['submission-id']
        updates = packet['cases']
        # max_position = max(map(itemgetter('position'), updates))

        # if not Submission.objects.filter(id=id).update(current_testcase=max_position + 1):
        #     logger.warning('Unknown submission: %s', id)
        #     json_log.error(self._make_json_log(packet, action='test-case', info='unknown submission'))
        #     return

        try:
            submission = Submission.objects.get(id=id)
        except Submission.DoesNotExist:
            logger.warning('Unknown submission: %s', id)
            json_log.error(self._make_json_log(packet, action='test-case', info='unknown submission'))
            return

        # bulk_test_case_updates = []
        status_codes = ['SC', 'AC', 'WA', 'MLE', 'TLE', 'IR', 'RTE', 'OLE']

        for result in updates:
            # test_case = SubmissionTestCase(submission_id=id, case=result['position'])
            # status = result['status']
            # if status & 4:
            #     test_case.status = 'TLE'
            # elif status & 8:
            #     test_case.status = 'MLE'
            # elif status & 64:
            #     test_case.status = 'OLE'
            # elif status & 2:
            #     test_case.status = 'RTE'
            # elif status & 16:
            #     test_case.status = 'IR'
            # elif status & 1:
            #     test_case.status = 'WA'
            # elif status & 32:
            #     test_case.status = 'SC'
            # else:
            #     test_case.status = 'AC'
            # test_case.time = result['time']
            # test_case.memory = result['memory']
            # test_case.points = result['points']
            # test_case.total = result['total-points']
            # test_case.batch = self.batch_id if self.in_batch else None
            # test_case.feedback = (result.get('feedback') or '')[:max_feedback]
            # test_case.extended_feedback = result.get('extended-feedback') or ''
            # test_case.output = result['output']
            # bulk_test_case_updates.append(test_case)
            if self.in_batch:
                if self._non_scaled_points is None:
                    self._non_scaled_points = result['points']
                else:
                    self._non_scaled_points = min(self._non_scaled_points, result['points'])
                if self._non_scaled_total is None:
                    self._non_scaled_total = result['total-points']
                else:
                    self._non_scaled_total = max(self._non_scaled_total, result['total-points'])
            else:
                submission.non_scaled_points += result['points']
                submission.non_scaled_total += result['total-points']
            submission.time = max(submission.time, result['time'])
            submission.memory = max(submission.memory, result['memory'])
            status = result['status']
            if status & 4:
                status_index = 4
            elif status & 8:
                status_index = 3
            elif status & 64:
                status_index = 7
            elif status & 2:
                status_index = 6
            elif status & 16:
                status_index = 5
            elif status & 1:
                status_index = 2
            elif status & 32:
                status_index = 0
            else:
                status_index = 1
            submission.internal_result = max(submission.internal_result, status_index)

            # json_log.info(self._make_json_log(
            #     packet, action='test-case', case=test_case.case, batch=test_case.batch,
            #     time=test_case.time, memory=test_case.memory, feedback=test_case.feedback,
            #     extended_feedback=test_case.extended_feedback, output=test_case.output,
            #     points=test_case.points, total=test_case.total, status=test_case.status,
            #     voluntary_context_switches=result.get('voluntary-context-switches', 0),
            #     involuntary_context_switches=result.get('involuntary-context-switches', 0),
            #     runtime_version=result.get('runtime-version', ''),
            # ))

        submission.save()

        # do_post = True

        # if id in self.update_counter:
        #     cnt, reset = self.update_counter[id]
        #     cnt += 1
        #     if time.monotonic() - reset > UPDATE_RATE_TIME:
        #         del self.update_counter[id]
        #     else:
        #         self.update_counter[id] = (cnt, reset)
        #         if cnt > UPDATE_RATE_LIMIT:
        #             do_post = False
        # if id not in self.update_counter:
        #     self.update_counter[id] = (1, time.monotonic())
        #
        # if do_post:
        #     event.post('sub_%s' % Submission.get_id_secret(id), {
        #         'type': 'test-case',
        #         'id': max_position,
        #     })
        #     self._post_update_submission(id, state='test-case')
        #
        # SubmissionTestCase.objects.bulk_create(bulk_test_case_updates)

    def on_internal_error(self, packet):
        try:
            raise ValueError('\n\n' + packet['message'])
        except ValueError:
            logger.exception('Judge %s failed while handling submission %s', self.name, packet['submission-id'])
        self._free_self(packet)

        id = packet['submission-id']
        if Submission.objects.filter(id=id).update(status='IE', result='IE', error=packet['message']):
            # event.post('sub_%s' % Submission.get_id_secret(id), {'type': 'internal-error'})
            # self._post_update_submission(id, 'internal-error', done=True)
            # json_log.info(self._make_json_log(packet, action='internal-error', message=packet['message'],
            #                                   finish=True, result='IE'))
            pass
        else:
            logger.warning('Unknown submission: %s', id)
            json_log.error(self._make_json_log(packet, action='internal-error', info='unknown submission',
                                               message=packet['message'], finish=True, result='IE'))

    def on_submission_terminated(self, packet):
        logger.info('%s: Submission aborted: %s', self.name, packet['submission-id'])
        self._free_self(packet)

        if Submission.objects.filter(id=packet['submission-id']).update(status='AB', result='AB', points=0):
            # event.post('sub_%s' % Submission.get_id_secret(packet['submission-id']), {'type': 'aborted-submission'})
            # self._post_update_submission(packet['submission-id'], 'terminated', done=True)
            # json_log.info(self._make_json_log(packet, action='aborted', finish=True, result='AB'))
            pass
        else:
            logger.warning('Unknown submission: %s', packet['submission-id'])
            json_log.error(self._make_json_log(packet, action='aborted', info='unknown submission',
                                               finish=True, result='AB'))

    def on_submission_acknowledged(self, packet):
        pass

    def on_ping_response(self, packet):
        pass

    # Called when there are changes to problem directories
    def on_supported_problems(self, packet):
        logger.info('%s: Updated problem list', self.name)
        self._tasks = packet['problems']
        self.tasks = dict(self._tasks)
        if not self.working:
            self.judges.update_problems(self)

        self.judge.tasks.set(TaskData.objects.filter(judge_code__in=list(self.tasks.keys())))
        json_log.info(self._make_json_log(action='update-problems', count=len(self.tasks)))

    # Return True if this judge can resolve submissions from the mentioned task
    def can_judge(self, task, executor, judge_id=None):
        return task in self.tasks and executor in self.executors and (not judge_id or self.name == judge_id)

    def submit(self, id, problem, language, source):
        try:
            time_limit, memory_limit, user_id = Submission.objects.filter(id=id).values_list(
                'task__time_limit',
                'task__memory_limit',
                'user_id',
            ).get()
        except Submission.DoesNotExist:
            logger.error('Submission vanished: %s', id)
            json_log.error(self._make_json_log(
                sub=self._working, action='request',
                info='submission vanished when fetching info',
            ))
            return
        self._working = id
        # self._no_response_job = threading.Timer(20, self._kill_if_no_response)
        self.send({
            'name': 'submission-request',
            'submission-id': id,
            'problem-id': problem,
            'language': language,
            'source': source,
            'time-limit': time_limit,
            'memory-limit': memory_limit,
            'short-circuit': False,
            'meta': {
                'pretests-only': False,
                'in-contest': 0,
                'attempt-no': 1,
                'user': user_id,
            },
        })
