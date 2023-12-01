# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import unittest
from unittest.mock import MagicMock, patch
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.services.graph_construction.graph_service import GraphService
from app.services.graph_construction.pre_find_symbol_connectivities import pre_find_symbol_connectivities
from app.services.graph_construction.config.symbol_node_keys_config import SymbolNodeKeysConfig

class TestPreFindSymbolConnectivitiesUnit(unittest.TestCase):
    @patch('app.services.graph_construction.pre_find_symbol_connectivities.does_string_contain_at_least_one_number_and_one_letter')
    @patch('app.services.graph_construction.pre_find_symbol_connectivities.is_symbol_text_invalid')
    def test_happy_path(self, mock_is_symbol_text_invalid, mock_does_string_contain_at_least_one_number_and_one_letter):
        # arrange
        def is_symbol_text_invalid(text: str):
            if text.startswith('invalid'):
                return True
            return False

        def does_string_contain_at_least_one_number_and_one_letter(text: str):
            if text is None:
                return False
            return text.isalnum()

        mock_is_symbol_text_invalid.side_effect = is_symbol_text_invalid
        mock_does_string_contain_at_least_one_number_and_one_letter.side_effect = does_string_contain_at_least_one_number_and_one_letter

        arrow_symbol_label = 'arrow'
        valve_symbol_label = 'valve'
        flow_direction_asset_prefixes = set(['Equip', 'Connector'])

        graph_service = MagicMock(GraphService)
        graph_service.get_symbol_nodes.return_value = [
            ('1', {SymbolNodeKeysConfig.LABEL_KEY: arrow_symbol_label}), # will be continued on since it's an arrow
            ('2', {SymbolNodeKeysConfig.LABEL_KEY: 'equip/1'}), # will be continued on since it does not have text associated key
            ('3', {SymbolNodeKeysConfig.LABEL_KEY: 'valve/6', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: None}), # will be continued on since text associated is None
            ('4', {SymbolNodeKeysConfig.LABEL_KEY: 'valve/1', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'valve1' }),
            ('5', {SymbolNodeKeysConfig.LABEL_KEY: 'valve/2', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'valve2' }),
            ('6', {SymbolNodeKeysConfig.LABEL_KEY: 'equip/3', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'equip3' }),
            ('7', {SymbolNodeKeysConfig.LABEL_KEY: 'connector/1', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'connector1' }),
            ('8', {SymbolNodeKeysConfig.LABEL_KEY: 'sensor/1', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'sendor1' }),
            ('9', {SymbolNodeKeysConfig.LABEL_KEY: 'valve/4', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'invalid2' }),
            ('10', {SymbolNodeKeysConfig.LABEL_KEY: 'equip/valve/4', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'valid2' }),
        ]

        symbol_label_prefixes_with_text = {'equip/', 'connector/', 'valve/'}

        # act
        result = pre_find_symbol_connectivities(
            graph_service,
            arrow_symbol_label,
            flow_direction_asset_prefixes,
            valve_symbol_label,
            symbol_label_prefixes_with_text)

        # asserts
        assert result.asset_valve_symbol_ids == {'4', '5'}
        assert result.flow_direction_asset_ids == {'6', '7', '10'}
        assert result.asset_symbol_ids == {'4', '5', '6', '7', '10'}


class TestPreFindSymbolConnectivitiesComponent(unittest.TestCase):
    def test_happy_path(self):
        # arrange
        arrow_symbol_label = 'arrow'
        valve_symbol_label = 'valve'
        flow_direction_asset_prefixes = set(['Equip', 'Connector'])

        graph_service = MagicMock(GraphService)
        graph_service.get_symbol_nodes.return_value = [
            ('1', {SymbolNodeKeysConfig.LABEL_KEY: arrow_symbol_label}), # will be continued on since it's an arrow
            ('2', {SymbolNodeKeysConfig.LABEL_KEY: 'equip/1'}), # will be continued on since it does not have text associated key
            ('3', {SymbolNodeKeysConfig.LABEL_KEY: 'valve/6', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: None}), # will be continued on since text associated is None
            ('4', {SymbolNodeKeysConfig.LABEL_KEY: 'valve/1', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'valve-1' }),
            ('5', {SymbolNodeKeysConfig.LABEL_KEY: 'valve/2', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'valve-2' }),
            ('6', {SymbolNodeKeysConfig.LABEL_KEY: 'equip/3', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'equip-3' }),
            ('7', {SymbolNodeKeysConfig.LABEL_KEY: 'connector/1', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'connector-1' }),
            ('8', {SymbolNodeKeysConfig.LABEL_KEY: 'sensor/1', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'sendor-1' }),
            ('9', {SymbolNodeKeysConfig.LABEL_KEY: 'valve/4', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: '2\"x1\"℃' }),
            ('10', {SymbolNodeKeysConfig.LABEL_KEY: 'equip/valve/4', SymbolNodeKeysConfig.TEXT_ASSOCIATED_KEY: 'valid-2' }),
        ]

        symbol_label_prefixes_with_text = {'equip/', 'connector/', 'valve/'}

        # act
        result = pre_find_symbol_connectivities(
            graph_service,
            arrow_symbol_label,
            flow_direction_asset_prefixes,
            valve_symbol_label,
            symbol_label_prefixes_with_text)

        # asserts
        assert result.asset_valve_symbol_ids == {'4', '5'}
        assert result.flow_direction_asset_ids == {'6', '7', '10'}
        assert result.asset_symbol_ids == {'4', '5', '6', '7', '10'}
