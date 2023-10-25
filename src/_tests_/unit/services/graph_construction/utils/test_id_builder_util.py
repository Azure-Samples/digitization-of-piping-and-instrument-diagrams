import os
import sys
import unittest
import parameterized

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))
from app.models.enums.graph_node_type import GraphNodeType
from app.services.graph_construction.utils import id_builder_util


class TestGetIntIdFromNodeId(unittest.TestCase):
    @parameterized.parameterized.expand([
        ('s-1', 1),
        ('l-2', 2),
        ('l-t-1', 1)
    ])
    def test_happy_path(self, node_id, expected_int_id):
        # act
        actual_int_id = id_builder_util.get_int_id_from_node_id(node_id)

        # assert
        self.assertEqual(actual_int_id, expected_int_id)


class TestCreateNodeId(unittest.TestCase):
    @parameterized.parameterized.expand([
        (GraphNodeType.line, 1, 'l-1'),
        (GraphNodeType.symbol, 2, 's-2')
    ])
    def test_happy_path(self, node_type, int_id, expected_node_id):
        # act
        actual_node_id = id_builder_util.create_node_id(node_type, int_id)

        # assert
        self.assertEqual(actual_node_id, expected_node_id)

    def test_when_unknown_node_type_raises_exception(self):
        # arrange
        node_type = GraphNodeType.unknown
        int_id = 1

        # act
        with self.assertRaises(Exception) as e:
            id_builder_util.create_node_id(node_type, int_id)

        # assert
        self.assertEqual(str(e.exception), f'Unknown node type: {node_type}')


class TestGetNodeTypeFromNodeId(unittest.TestCase):
    @parameterized.parameterized.expand([
        ('l-1', GraphNodeType.line),
        ('s-2', GraphNodeType.symbol),
        ('t-3', GraphNodeType.text)
    ])
    def test_happy_path(self, node_id, expected_node_type):
        # act
        actual_node_id = id_builder_util.get_node_type_from_node_id(node_id)

        # assert
        self.assertEqual(actual_node_id, expected_node_type)
