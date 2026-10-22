
# Write diagram syntax <a id="write-diagram-syntax"></a>

Mermaid syntax is plain text with a defined structure. Once you understand the basics, you can build and edit any diagram without touching the AI panel — and you’ll know exactly what to change when a diagram needs updating.
This guide covers flowchart syntax in depth. For other diagram types, the same principles apply; the OSS docs have full syntax references for every type. [Browse the OSS syntax docs →](https://mermaid.js.org/intro/)
## How syntax works <a id="how-syntax-works"></a>

Every diagram starts with a type declaration that tells Mermaid what kind of diagram to render:
```plaintext
flowchart LR
sequenceDiagram
erDiagram
mindmap
gantt
```

Everything that follows defines the content — nodes, connections, labels, styles, and groupings. The diagram renders in real time as you type in the editor.
## Flowchart direction <a id="flowchart-direction"></a>

For flowcharts, the direction comes right after the type declaration:
```mermaid
block-beta
columns 3
  h_0["<b>Direction</b>"]
  h_1["<b>Code</b>"]
  h_2["<b>When to use</b>"]
  c_0_0["Left to right"]
  c_0_1["LR"]
  c_0_2["Processes, workflows, timelines"]
  c_1_0["Top to bottom"]
  c_1_1["TD or TB"]
  c_1_2["Hierarchies, org charts, decision trees"]
  c_2_0["Bottom to top"]
  c_2_1["BT"]
  c_2_2["Reverse hierarchies"]
  c_3_0["Right to left"]
  c_3_1["RL"]
  c_3_2["Less common — specific layout needs"]
```

| Direction | Code | When to use |
|---|---|---|
| Left to right | LR | Processes, workflows, timelines |
| Top to bottom | TD or TB | Hierarchies, org charts, decision trees |
| Bottom to top | BT | Reverse hierarchies |
| Right to left | RL | Less common — specific layout needs |


Direction has a bigger impact on readability than most people expect. The same diagram can be clear or cluttered depending on which way it flows. If a layout looks off, try changing the direction before adjusting anything else.
## Nodes <a id="nodes"></a>

Nodes are the building blocks of a flowchart. Shape carries meaning — use it deliberately.
```mermaid
block-beta
columns 3
  h_0["<b>Syntax</b>"]
  h_1["<b>Shape</b>"]
  h_2["<b>When to use</b>"]
  c_0_0["A\(Label\)"]
  c_0_1["Rectangle"]
  c_0_2["Default — steps, actions, tasks"]
  c_1_0["A(Label)"]
  c_1_1["Rounded rectangle"]
  c_1_2["Softer steps, start and end points"]
  c_2_0["A\(Label\)"]
  c_2_1["Diamond"]
  c_2_2["Decisions with branching paths"]
  c_3_0["A((Label))"]
  c_3_1["Circle"]
  c_3_2["Events, endpoints, loop connectors"]
  c_4_0["A\(/Label/\)"]
  c_4_1["Parallelogram"]
  c_4_2["Input or output"]
  c_5_0["A\((Label)\)"]
  c_5_1["Cylinder"]
  c_5_2["Databases, data stores"]
  c_6_0["A\(\(Label\)\)"]
  c_6_1["Subroutine"]
  c_6_2["Subprocess or referenced flow"]
  c_7_0["A\>Label\)"]
  c_7_1["Asymmetric"]
  c_7_2["Flags, tags"]
```

| Syntax | Shape | When to use |
|---|---|---|
| A\[Label\] | Rectangle | Default — steps, actions, tasks |
| A(Label) | Rounded rectangle | Softer steps, start and end points |
| A\{Label\} | Diamond | Decisions with branching paths |
| A((Label)) | Circle | Events, endpoints, loop connectors |
| A\[/Label/\] | Parallelogram | Input or output |
| A\[(Label)\] | Cylinder | Databases, data stores |
| A\[\[Label\]\] | Subroutine | Subprocess or referenced flow |
| A\>Label\] | Asymmetric | Flags, tags |


Node IDs and labels are separate. The ID is used to reference the node in connections — the label is what renders in the diagram. Define the label once and use the ID everywhere else:
flowchart LR
    A[Content brief] --> B[Draft]
    B --> C{Ready for review?}
    C -->|Yes| D[Send to reviewer]
    C -->|No| B
    D --> E[Published]
Tip: Don't use the word end in all lowercase as a node ID or label — it's a reserved word and breaks the parser. Use End, END, or a different word entirely.
## Connections <a id="connections"></a>

Connection type carries meaning. Use the right one for what you’re showing.
```mermaid
block-beta
columns 3
  h_0["<b>Syntax</b>"]
  h_1["<b>Renders as</b>"]
  h_2["<b>When to use