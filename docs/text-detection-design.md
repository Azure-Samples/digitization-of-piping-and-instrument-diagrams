# Text detection design

This document presents the proposed design for text detection on P&IDs in this project.

## Summary

The text detection workflow has two key goals:

- Recognize and store the text associated with each symbol in a P&ID image. These will be used as the unique identifiers for each detected symbol in the constructed graph.
- Recognize and store all text in a P&ID image. This will be used as a mask in the initial pre-processing for line detection to remove all extraneous features before the line detection heuristic is applied.

## Azure AI Services for OCR

[Azure AI Services](https://learn.microsoft.com/en-us/azure/ai-services/what-are-ai-services) (formerly known as Azure Cognitive Services) are cloud-based artificial intelligence (AI) services that implement a wide range of cognitive intelligence functionalities through REST APIs and SDKs.
The text recognition logic in this project will be powered by [Azure AI Document Intelligence](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview?view=doc-intel-3.0.0) (formerly known as Azure Form Recognizer), which exposes APIs for [Optical Character Recognition (OCR)](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-read?view=doc-intel-3.0.0).

OCR is performed by making a single API call to the [Document Analysis API](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-analyze-document-response?view=doc-intel-3.0.0#analyze-document-request) that has a URL pointer to the image to analyze.

The API returns a [JSON body](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-layout?view=doc-intel-3.0.0#pages-extraction) containing the [content, layout, style, and semantic elements](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-analyze-document-response?view=doc-intel-3.0.0#analyze-response) of the image analyzed. Based on the project requirements, the relevant results include each piece of text recognized, the bounding box coordinates of that text in the image, and the confidence score of the OCR results;
these can be further analyzed to associate text with symbols, as we'll discuss in the [proposed flow](#proposed-text-detection-workflow).

Additionally, due to the nature of the P&ID documents, [high-resolution extraction capability](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-add-on-capabilities?view=doc-intel-3.0.0#high-resolution-extraction) will be enabled to recognize small text from large-size documents.

For more information on the definition of the Read OCR model, see the documentation linked [here](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-read?view=doc-intel-3.0.0).

## Relevant infrastructure

We will need to deploy an [Azure Form Recognizer](https://portal.azure.com/#create/Microsoft.CognitiveServicesFormRecognizer) resource.

This can be deployed into a specified virtual network and subnet for purposes of network security.
More information on configuring Azure Form Recognizer for use with virtual networks can be found in the [Azure docs](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/managed-identities-secured-access?view=doc-intel-3.0.0#configure-private-endpoints-for-access-from-vnets).

To access the Form Recognizer resource, the application's service principal will be assigned to the
[`Cognitive Services User` role](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-formrecognizer-readme?view=azure-python#create-the-client-with-an-azure-active-directory-credential). Thus,
API calls that authenticate with `DefaultAzureCredential` do not require the API access key of the created Form Recognizer resource; they only requires
the endpoint.

## Image pre-processing strategies + experiment results

Grayscaling and binarization are two commonly used image processing techniques to preprocess images before further analysis.

- Grayscaling is the process of converting a color image into a grayscale image, where each pixel has a single intensity value
representing the brightness of that pixel. Grayscale images are simpler to process and analyze than color images.
- Binarization, on the other hand, is the process of converting a grayscale or color image into a binary image, where each pixel is
either black or white.
This is done by thresholding the image, where all pixels with intensity values below a certain threshold are set to black, and all
pixels with intensity values above the threshold are set to white.

The text detection service will have a configurable flag to set whether pre-processing is enabled prior to submitting the image to Azure Computer Vision for OCR.
The pre-processing implemented in this project will be a simple grayscale conversion + binarization;
due to the variability of results based on image resolution, we will not implement erosion/dilation

This will also serve as a placeholder so that the developers will be able to implement further image pre-processing in the future if desired.

For more details on the techniques explored and experiment results, see [this writeup](../spikes/text-detection/image-preprocessing/README.md) in the `spikes/text-detection` directory.

We also investigated image tiling as an option for pre-processing images prior to OCR;
we didn't see any significant benefit to accuracy from it, and have thus decided not to implement it for simplicity.
This decision is documented in [this writeup](../spikes/ocr-tiling/ReadMe.md) in the `spikes/ocr-tiling` directory.

## Proposed text detection workflow

1. Download original P&ID image from blob storage
1. Apply image preprocessing such as grayscale and binarization
1. Detect text sending a single OCR request for the entire image (text lines can be broken up at this moment)
1. Using the latest symbol detection results, iterate over each symbol detection item and apply logic to
find the associated text of a symbol. There are a few priority rules when merging texts:
    - Check which text is within symbols. If there are multiple texts within the symbol, the text will be merged
    into a single text
    - Check which text is outside/nearby the symbols
1. Transform bounding box to normalized data.
1. We'll hold this transformation data into the `symbol_and_text_associated_list` variable.
1. Transform previous data into a new list keeping only text data (no symbols). We'll hold this data in
`all_text_list` variable.
1. Draw on original text detected (displaying with a color the ones are part of a symbols and the ones that are now), then store
image output in blob storage.
1. Return response to user including both output lists.

### API contracts

#### POST TextDetection [/api/pid-digitization/text-detection/{pid_id}]

This endpoint takes in the P&ID image id to download the original image and recognize the texts of the image. Additionally,
it takes in the corrected symbol detected inference results which will be stored and used to associate a text with a symbol.

##### POST TextDetection Input

The request must contain the following data:

- P&ID image id (path variable)
- Corrected symbol detection inference results (body)

Here is a request example:

```text
POST /api/pid-digitalization/text-detection/5

Request body:
{
    "image_url": "pid2.png",
    "image_details": {
      "format": "png",
      "width": 1388,
      "height": 781
    },
    "label": [
      {
        "topX": 0.5067512555,
        "topY": 0.72654658,
        "bottomX": 0.5136717032,
        "bottomY": 0.7377242533,
        "id": 0,
        "label": "24",
        "score": 0.9782005548
      },
      ...
  ]
}
```

##### POST TextDetection Output

The endpoint stores the corrected symbol detected inference results and some of the intermediate
text detection results in blob storage. These results include:

- All text detected on a P&ID image
- Only text associated with each symbol on a P&ID image
- [If debug] the P&ID input image with the bounding boxes drawn on symbols in the image

The response from the endpoint is a `JSON` object that has the following format:

```json
{
    "image_url": "pid2.png",
    "image_details": {
      "format": "png",
      "width": 1388,
      "height": 781
    },
    "all_text_list": [
        {
            "text": "GLR",
            "topX": 0.5067512555,
            "topY": 0.72654658,
            "bottomX": 0.5136717032,
            "bottomY": 0.7377242533,
        },
        ...
    ],
    "symbol_and_text_associated_list": [
        {
            "id": "<symbol_id>",
            "topX": 0.4067512554,
            "topY": 0.42654657,
            "bottomX": 0.4136717031,
            "bottomY": 0.6377242532,
            "text_associated": "ZLC"
        },
        ...
    ]
}
```

The output contains two lists:

- `all_text_list` contains all text on the image
- `symbol_and_text_associated_list` contains the list of symbols with its text associated

#### GET TextDetection [/api/pid-digitization/text-detection/{pid_id}]

This endpoint takes in the P&ID image id to get the latest recognized text stored.

##### GET TextDetection Input

The request must contain the following data:

- P&ID image id (path variable)

Here is a request example:

```text
GET /api/pid-digitalization/text-detection/5
```

##### GET TextDetection Output

Same output as [POST TextDetection](#post-textdetection-output)

## Further reading

- [Azure Computer Vision OCR](https://learn.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-ocr)

