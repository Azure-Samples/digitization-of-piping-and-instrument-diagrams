# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
import argparse
import json
import cv2
from typing import Union
from app.models.graph_construction.base_connected_symbols_item import BaseConnectedSymbolsItem
from app.models.graph_construction.connected_symbols_item import ConnectedSymbolsItem
from app.models.graph_construction.graph_construction_response import GraphConstructionInferenceResponse
from app.models.bounding_box import BoundingBox


STARTING_ASSET_COLOR = (255, 0, 0)  # dark blue
CONNECTED_ASSET_COLOR = (0, 128, 0)  # dark green
VISITED_ASSET_COLOR = (192, 192, 192)


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--image-path',
        type=str,
        dest='image_path',
        help='The path to the image',
        required=True
    )
    parser.add_argument(
        '--asset-connectivity-path',
        type=str,
        dest='asset_connectivity_path',
        help='The path to the asset connectivity json file',
        required=True
    )
    parser.add_argument(
        '--starting-asset-id',
        type=int,
        dest='starting_asset_id',
        help='The starting asset id',
        required=True
    )
    parser.add_argument(
        '--output-folder-path',
        type=str,
        dest='output_folder_path',
        help='The output path',
        required=True
    )

    args = parser.parse_args()
    return args


def _denormalize_bounding_box(
    bounding_box: BoundingBox,
    image_height: int,
    image_width: int
):
    return BoundingBox(
        topX=int(bounding_box.topX * image_width),
        topY=int(bounding_box.topY * image_height),
        bottomX=int(bounding_box.bottomX * image_width),
        bottomY=int(bounding_box.bottomY * image_height)
    )


def _draw_asset_on_image(
    image: cv2.Mat,
    image_height: int,
    image_width: int,
    asset: BaseConnectedSymbolsItem,
    color: tuple[int, int, int]
):
    asset_bounding_box = _denormalize_bounding_box(
        asset.bounding_box,
        image_height,
        image_width
    )

    cv2.rectangle(
        img=image,
        pt1=(int(asset_bounding_box.topX), int(asset_bounding_box.topY)),
        pt2=(int(asset_bounding_box.bottomX), int(asset_bounding_box.bottomY)),
        color=color,
        thickness=4
    )
    cv2.putText(
        img=image,
        text=str(asset.id),
        org=(int(asset_bounding_box.topX), int(asset_bounding_box.topY)),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=1,
        color=color,
        thickness=3
    )


def _draw_bounding_box_on_image(
    image: cv2.Mat,
    image_height: int,
    image_width: int,
    bounding_box: BoundingBox,
    color: tuple[int, int, int]
):
    bounding_box = _denormalize_bounding_box(
        bounding_box,
        image_height,
        image_width
    )

    cv2.rectangle(
        img=image,
        pt1=(int(bounding_box.topX), int(bounding_box.topY)),
        pt2=(int(bounding_box.bottomX), int(bounding_box.bottomY)),
        color=color,
        thickness=2
    )


def main(
    image: cv2.Mat,
    asset_connectivity: ConnectedSymbolsItem,
    output_path: str
):
    print('Starting program to show paths')
    image_height, image_width, _ = image.shape

    for connected_asset in asset_connectivity.connections:
        _draw_asset_on_image(
            image,
            image_height,
            image_width,
            connected_asset,
            CONNECTED_ASSET_COLOR
        )

        for visited_element in connected_asset.segments:
            _draw_bounding_box_on_image(
                image,
                image_height,
                image_width,
                visited_element,
                VISITED_ASSET_COLOR
            )

    _draw_asset_on_image(
        image,
        image_height,
        image_width,
        asset_connectivity,
        STARTING_ASSET_COLOR
    )

    print(f'Saving image to {output_path}')
    cv2.imwrite(output_path, image)


if __name__ == "__main__":
    args = _get_args()
    image_path = args.image_path
    asset_connectivity_path = args.asset_connectivity_path
    starting_asset_id = args.starting_asset_id
    output_folder_path = args.output_folder_path

    if not os.path.exists(image_path):
        raise Exception(f'Image path "{image_path}" does not exist')

    if not os.path.exists(asset_connectivity_path):
        raise Exception(f'Asset connectivity path "{asset_connectivity_path}" does not exist')

    with open(asset_connectivity_path, 'r') as f:
        asset_connectivity = json.load(f)

    if not os.path.exists(output_folder_path):
        print(f'Output folder path "{output_folder_path}" does not exist. Creating it...')
        os.makedirs(output_folder_path, exist_ok=True)

    output_file_name = os.path.basename(image_path)
    output_file_name = os.path.splitext(output_file_name)[0]
    output_file_name = f'{output_file_name}_{starting_asset_id}.png'
    output_path = os.path.join(output_folder_path, output_file_name)

    asset_connectivity: GraphConstructionInferenceResponse = GraphConstructionInferenceResponse \
        .parse_obj(asset_connectivity) \
        .connected_symbols
    image = cv2.imread(image_path)

    # check if starting asset is in asset connectivity
    connected_asset_item: Union[ConnectedSymbolsItem, None] = None
    for elem in asset_connectivity:
        if elem.id == starting_asset_id:
            connected_asset_item = elem
            break

    if not connected_asset_item:
        raise Exception(f'Starting symbol "{starting_asset_id}" not found in asset connectivity')

    main(
        image,
        connected_asset_item,
        output_path)
