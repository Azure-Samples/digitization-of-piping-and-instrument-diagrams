# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import unittest
from unittest.mock import MagicMock, patch, call
import sys

from app.models.enums.graph_node_type import GraphNodeType
from app.models.text_detection.symbol_and_text_associated import SymbolAndTextAssociated
from app.services.graph_construction.connect_symbols_that_are_close \
    import connect_symbols_that_are_close

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


class TestConnectSymbolsThatAreClose(unittest.TestCase):
    graph_symbol_to_symbol_distance_threshold = 0.01

    def test_happy_path_connect_symbols_that_are_close(self):
        # arrange
        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(
                id=1,
                label='Equipment/Heat transfer/Finned heat exchanger',
                score=None,
                topX=0.1,
                topY=0.1,
                bottomX=0.4,
                bottomY=0.4,
                text_associated='2C-106',
            ),
            SymbolAndTextAssociated(
                id=2,
                label='Piping/Fittings/Flanged connection',
                score=None,
                topX=0.2,
                topY=0.4,
                bottomX=0.3,
                bottomY=0.5,
                text_associated=None,
            ),
            SymbolAndTextAssociated(
                id=3,
                label='Instrument/Indicator/Field mounted discrete indicator',
                score=None,
                topX=0.7,
                topY=0.7,
                bottomX=0.8,
                bottomY=0.8,
                text_associated='PSV 1056A',
            )
        ]

        graph_service_mock = MagicMock()
        graph_service_mock.get_degree = MagicMock(return_value=1)

        config_mock = MagicMock()
        config_mock.symbol_label_prefixes_to_connect_if_close = \
            {'Equipment', 'Instrument/Valve/', 'Piping/Fittings/Mid arrow flow direction'}
        config_mock.graph_symbol_to_symbol_overlap_region_threshold = 0.5

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                  config_mock):
            connect_symbols_that_are_close(graph_service_mock, text_and_symbols_associated_list, self.graph_symbol_to_symbol_distance_threshold)

        # assert
        graph_service_mock.add_node.assert_called_once_with('l-s-1-s-2', node_type=GraphNodeType.line, startX=0.25, startY=0.25, endX=0.25, endY=0.45)
        graph_service_mock.add_edge.assert_called_once_with('s-1', 's-2')


    def test_connect_symbols_that_are_close_no_low_degree(self):
        # arrange
        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(
                id=1,
                label='Equipment/Heat transfer/Finned heat exchanger',
                score=None,
                topX=0.1,
                topY=0.1,
                bottomX=0.4,
                bottomY=0.4,
                text_associated='2C-106',
            ),
            SymbolAndTextAssociated(
                id=2,
                label='Piping/Fittings/Flanged connection',
                score=None,
                topX=0.2,
                topY=0.4,
                bottomX=0.3,
                bottomY=0.5,
                text_associated=None,
            ),
            SymbolAndTextAssociated(
                id=3,
                label='Instrument/Indicator/Field mounted discrete indicator',
                score=None,
                topX=0.7,
                topY=0.7,
                bottomX=0.8,
                bottomY=0.8,
                text_associated='PSV 1056A',
            )
        ]

        graph_service_mock = MagicMock()
        graph_service_mock.get_degree = MagicMock(return_value=2)

        config_mock = MagicMock()
        config_mock.symbol_label_prefixes_to_connect_if_close = \
            {'Equipment', 'Instrument/Valve/', 'Piping/Fittings/Mid arrow flow direction'}
        config_mock.graph_symbol_to_symbol_overlap_region_threshold = 0.5

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                  config_mock):
            connect_symbols_that_are_close(graph_service_mock, text_and_symbols_associated_list, self.graph_symbol_to_symbol_distance_threshold)

        # assert
        graph_service_mock.add_node.assert_not_called()
        graph_service_mock.add_edge.assert_not_called()


    def test_connect_symbols_that_are_close_symbols_are_not_close(self):
        # arrange
        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(
                id=1,
                label='Equipment/Heat transfer/Finned heat exchanger',
                score=None,
                topX=0.1,
                topY=0.1,
                bottomX=0.4,
                bottomY=0.4,
                text_associated='2C-106',
            ),
            SymbolAndTextAssociated(
                id=2,
                label='Piping/Fittings/Flanged connection',
                score=None,
                topX=0.2,
                topY=0.5,
                bottomX=0.3,
                bottomY=0.6,
                text_associated=None,
            ),
            SymbolAndTextAssociated(
                id=3,
                label='Instrument/Indicator/Field mounted discrete indicator',
                score=None,
                topX=0.7,
                topY=0.7,
                bottomX=0.8,
                bottomY=0.8,
                text_associated='PSV 1056A',
            )
        ]

        graph_service_mock = MagicMock()
        graph_service_mock.get_degree = MagicMock(return_value=1)

        config_mock = MagicMock()
        config_mock.symbol_label_prefixes_to_connect_if_close = \
            {'Equipment', 'Instrument/Valve/', 'Piping/Fittings/Mid arrow flow direction'}
        config_mock.graph_symbol_to_symbol_overlap_region_threshold = 0.5

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                  config_mock):
            connect_symbols_that_are_close(graph_service_mock,
                                           text_and_symbols_associated_list,
                                           self.graph_symbol_to_symbol_distance_threshold)

        # assert
        graph_service_mock.add_node.assert_not_called()
        graph_service_mock.add_edge.assert_not_called()


    def test_connect_symbols_that_are_close_none_in_symbol_label_prefixes(self):
        # arrange
        text_and_symbols_associated_list = [
            SymbolAndTextAssociated(
                id=1,
                label='Instrument/Indicator/Field mounted discrete indicator',
                score=None,
                topX=0.1,
                topY=0.1,
                bottomX=0.4,
                bottomY=0.4,
                text_associated='2C-106',
            ),
            SymbolAndTextAssociated(
                id=2,
                label='Instrument/Indicator/Field mounted discrete indicator',
                score=None,
                topX=0.2,
                topY=0.4,
                bottomX=0.3,
                bottomY=0.5,
                text_associated=None,
            ),
            SymbolAndTextAssociated(
                id=3,
                label='Instrument/Indicator/Field mounted discrete indicator',
                score=None,
                topX=0.7,
                topY=0.7,
                bottomX=0.8,
                bottomY=0.8,
                text_associated='PSV 1056A',
            )
        ]

        graph_service_mock = MagicMock()
        graph_service_mock.get_degree = MagicMock(return_value=1)

        config_mock = MagicMock()
        config_mock.symbol_label_prefixes_to_connect_if_close = \
            {'Equipment', 'Instrument/Valve/', 'Piping/Fittings/Mid arrow flow direction'}
        config_mock.graph_symbol_to_symbol_overlap_region_threshold = 0.5

        # act
        with patch("app.services.graph_construction.connect_lines_with_arrows.config",
                  config_mock):
            connect_symbols_that_are_close(graph_service_mock,
                                           text_and_symbols_associated_list,
                                           self.graph_symbol_to_symbol_distance_threshold)

        # assert
        graph_service_mock.add_node.assert_not_called()
        graph_service_mock.add_edge.assert_not_called()
