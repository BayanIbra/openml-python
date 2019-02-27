import numpy as np

from tests.test_tasks import OpenMLSupervisedTaskTest


class OpenMLLearningCurveTaskTest(OpenMLSupervisedTaskTest):

    def setUp(self):

        super(OpenMLLearningCurveTaskTest, self).setUp()
        self.task_id = 801
        self.estimation_procedure = 14

    def test_get_X_and_Y(self):

        X, Y = super(OpenMLLearningCurveTaskTest, self).test_get_X_and_Y()
        self.assertEqual((768, 8), X.shape)
        self.assertIsInstance(X, np.ndarray)
        self.assertEqual((768, ), Y.shape)
        self.assertIsInstance(Y, np.ndarray)
        self.assertEqual(Y.dtype, int)

    def test_download_task(self):

        task = super(OpenMLLearningCurveTaskTest, self).test_download_task()
        self.assertEqual(task.task_id, self.task_id)
        self.assertEqual(task.task_type_id, 3)
        self.assertEqual(task.dataset_id, 20)