# An Azure-based Solution for Digitization of Engineering Diagrams in Process Industry

There are standardized schematic illustrations of any process industry plant that show the interconnection of the process equipment, instrumentation used to control the process, and flow of the fluid and control signals. One of the most important reasons to digitize these schematic illustrations such as piping and instrumentation diagrams (P&IDs) or Process Flow Diagrams (PFDs)  into a graph data structure is to facilitate the analysis and manipulation of this process information. A graph data structure is a collection of nodes that have data and are connected to other nodes. By representing these diagrams as graphs, we can use various algorithms and methods to perform tasks such as finding the shortest paths, detecting cycles, computing transitive closures, and so on. These tasks can help us to optimize the process design, improve the system control, enhance safety and reliability, and reduce the cost and complexity of the process. Moreover, by digitizing into a graph data structure, we can also store additional data on the nodes and edges, such as labels, attributes, values, etc. This can help us to enrich the information content of the plant process diagram and make them more informative and comprehensive. 

The digitization process of these diagrams to a graph data structure involves several steps. First, the scanned image is pre-processed using image processing techniques to enhance the quality and remove the noise. Second, the core components of the diagrams, such as pipes, symbols, lines and text, are detected and extracted using various image processing and machine learning techniques. Third, the extracted components are associated with each other based on their spatial and semantic relationships. Fourth, the output data is validated and corrected based on the domain knowledge and rules of the process flow. Finally, the output data is converted into a graph data structure, where each node represents a component, and each edge represents a connection between components. The graph data structure can then be stored, queried, and manipulated using various algorithms and methods.


# Documentation

The `docs` folder of this repo contains the relevant documentation for the project at a high level and detailed information on the design and implementation of the inference service.
For additional details on the symbol detection model training and deployment, see the [documentation](https://github.com/Azure-Samples/MLOpsManufacturing/tree/main/samples/amlv2_pid_symbol_detection_train/docs).

## Pages

- [An Azure Architecture for Digitization of P&ID](docs/architecture.md): Gives an overview of the project context and overall architecture. Start here to get a better sense of the project as a whole and the high level data flow.
- [User guide to the inference service](docs/user-guide.md): Intended as a guide for end users of the system - this walks through the user flow, ways to run and make requests against the service, and high-level guidance for troubleshooting results.
- [Developer guide](docs/local_development_setup.md): Gives instructions on how developers can set up their local dev environments to work with this repo.
- Design documents for different components of the inference service gives more in-depth details on each component/feature of the inference service and its design considerations.
  - [Text detection](docs/text-detection-design.md)
  - [Line detection](docs/line-detection-design.md)
  - [Graph construction](docs/graph-construction-design.md)
  - [Arrow direction detection](/arrow-direction-detection-design.md)
  - [Process flow](docs/process-flow-design.md)
  - [Graph persistence](docs/design-db.md)
- API contracts and Postman collection: The exported Swagger spec for the inference web API, as well as a convenient [Postman](https://www.postman.com/) collection for the exposed endpoints of the inference service.
  - [Swagger API spec](docs/webapi-swagger.yaml)
  - [Postman collection](docs/postman/): Note that both the JSON collection and the environments will need to be imported.
- [SQL Graph DB for Storing P&IDs](docs/design-db.md): Gives details on the design of the SQL Graph DB used for storing the P&ID data.