from app.models.enums.graph_node_type import GraphNodeType


def get_int_id_from_node_id(string_id: str) -> int:
    '''Gets the int id from the string id.

    :param string_id: The string id
    :type string_id: str
    :return: The int id
    :rtype: int
    '''

    return int(string_id.split('-')[-1])


def create_node_id(node_type: GraphNodeType, int_id: int) -> str:
    '''Creates a string id from the int id.

    :param node_type: The type of the node
    :type node_type: GraphNodeType
    :param int_id: The int id
    :type int_id: int
    :return: The string id
    :rtype: str
    '''

    if node_type == GraphNodeType.line:
        return f'l-{int_id}'
    elif node_type == GraphNodeType.symbol:
        return f's-{int_id}'
    else:
        raise ValueError(f'Unknown node type: {node_type}')


def get_node_type_from_node_id(node_id: str) -> GraphNodeType:
    '''Gets the node type from the node id.

    :param node_id: The node id
    :type node_id: str
    :return: The node type
    :rtype: GraphNodeType
    '''

    if node_id.split('-')[0] == 's':
        return GraphNodeType.symbol
    elif node_id.split('-')[0] == 't':
        return GraphNodeType.text
    elif node_id.split('-')[0] == 'l':
        return GraphNodeType.line
    else:
        return GraphNodeType.unknown
