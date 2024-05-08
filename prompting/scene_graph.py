import re

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


class SceneObject:
    def __init__(self, id, attributes) -> None:
        self.id = id
        self.attributes = attributes

    def __repr__(self) -> str:
        return f"obj-{self.id}:[{', '.join(self.attributes)}]"


class SceneRelationship:
    def __init__(self, id, subject, predicate, object) -> None:
        self.id = id
        self.subject = subject
        self.predicate = predicate
        self.object = object

    def __repr__(self) -> str:
        return f"rel-{self.id}:({self.subject}, {self.predicate}, {self.object})"


class SceneGraph:
    def __init__(self, objects=None, relations=None) -> None:
        self._objects = objects
        self._relations = relations
        self.objects = {}
        self.relationships = []
        self.parse_args()

    def parse_args(self):
        if self._objects is not None:
            for obj in self._objects:
                label = obj['label'].replace(' ', '-')
                attributes = []
                for group, attrs in obj['attributes'].items():
                    a = [attr.replace(' ', '-') for attr in attrs]
                    attributes.extend(a)
                self.add_object(SceneObject(label, attributes))
        if self._relations is not None:
            for idx, rel in enumerate(self._relations):
                subject = rel['subject_name'].replace(' ', '-')
                predicate = rel['relation_name']
                obj = rel['object_name'].replace(' ', '-')

                # skil trivial relationships
                if 'same' in predicate:
                    continue

                # if either subject or object is not in the objects list, add them
                if subject not in self.objects:
                    self.add_object(SceneObject(subject, []))
                if obj not in self.objects:
                    self.add_object(SceneObject(obj, []))

                self.add_relationship(SceneRelationship(
                    idx, subject, predicate, obj))

    def add_object(self, obj):
        self.objects[obj.id] = obj

    def add_relationship(self, rel):
        self.relationships.append(rel)

    def to_json(self):
        return {
            'objects': {obj.id: obj.attributes for obj in self.objects.values()},
            'relationships': [(rel.subject, rel.predicate, rel.object) for rel in self.relationships]
        }

    def __repr__(self) -> str:
        objects_str = '; '.join([str(obj) for obj in self.objects.values()])
        relationships_str = '; '.join([str(rel) for rel in self.relationships])
        return f"{objects_str}; {relationships_str}"

    def visualize(self, save_path, title='Scene Graph', orig_img=None):
        G = nx.DiGraph()
        node_colors = []
        node_shapes = []

        # Add object nodes
        object_nodes = set()
        attribute_nodes = set()
        for obj_id, obj in self.objects.items():
            G.add_node(obj_id)
            object_nodes.add(obj_id)
            node_colors.append('skyblue')  # Object nodes color

            # Add attribute nodes related to this object
            for attr in obj.attributes:
                attr_id = f"{obj_id}_{attr}"
                G.add_node(attr_id)
                G.add_edge(obj_id, attr_id)
                node_colors.append('lightgreen')  # Attributes nodes color
                attribute_nodes.add(attr_id)

        # Add edges for relationships
        for rel in self.relationships:
            G.add_edge(rel.subject, rel.object, label=rel.predicate)

        # Draw the graph
        if orig_img is not None:
            plt.figure(figsize=(20, 10))

            plt.subplot(1, 2, 1)
            plt.imshow(orig_img)
            plt.axis('off')
            plt.title('Original Image')

            plt.subplot(1, 2, 2)
            plt.axis('off')
            plt.title(title)
        else:
            plt.figure(figsize=(10, 10))
            plt.title(title)

        # Layout the graph
        pos = nx.spring_layout(G)

        # Draw object nodes
        nx.draw_networkx_nodes(G, pos, nodelist=list(object_nodes), node_color='skyblue')

        # Draw attribute nodes
        nx.draw_networkx_nodes(G, pos, nodelist=list(attribute_nodes), node_color='lightgreen')

        # Draw edges
        nx.draw_networkx_edges(G, pos)

        # Labels for all nodes
        nx.draw_networkx_labels(G, pos)

        # Edge labels
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

        # Legend
        obj_patch = mpatches.Patch(color='skyblue', label='Objects')
        attr_patch = mpatches.Patch(color='lightgreen', label='Attributes')
        plt.legend(handles=[obj_patch, attr_patch])

        # Save the graph
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

        

    @staticmethod
    def parse(sentence):
        # Split the sentence into object and relationship declarations
        parts = sentence.split(';')

        # All parts starting with the 'obj-' prefix are object declarations
        object_declarations = [part.strip()
                               for part in parts if part.strip().startswith('obj-')]

        # All parts starting with the 'rel-' prefix are relationship declarations
        relationship_declarations = [
            part.strip() for part in parts if part.strip().startswith('rel-')]

        # Process object declarations
        objects = {}
        for decl in object_declarations:
            try:
                # Extract the object ID and attributes
                obj_id, attributes = decl.split(':')
                obj_id = obj_id.strip().replace('obj-', '')
                attributes = attributes.replace('[', '').replace(']', '').split(',')
                objects[obj_id] = [attr.strip() for attr in attributes]
            except Exception as e:
                print(f"Error parsing object: {decl}")
                print(e)

        # Process relationship declarations
        relationships = []
        for decl in relationship_declarations:
            try:
                # Extract the relationship ID, subject, predicate, and object
                rel_id, rel = decl.split(':')
                rel_id = rel_id.strip().replace('rel-', '')
                subj, pred, obj = re.search(r'\((.*), (.*), (.*)\)', rel).groups()
                subj = subj.strip()
                pred = pred.strip()
                obj = obj.strip()
                relationships.append((rel_id, subj, pred, obj))
            except Exception as e:
                print(f"Error parsing relationship: {decl}")
                print(e)

        # Construct the graph-like data structure
        graph = SceneGraph()
        for obj_id, attributes in objects.items():
            graph.add_object(SceneObject(obj_id, attributes))
        for i, subj_id, rel, obj_id in relationships:
            graph.add_relationship(SceneRelationship(i, subj_id, rel, obj_id))

        return graph
