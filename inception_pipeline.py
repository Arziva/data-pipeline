import requests
import json
import xml.etree.ElementTree as ET

def read_ids_from_file(file_path):
    with open(file_path, 'r') as file:
        ids = file.read().split(",")
        return ids

def create_id_string(ids):
    id_string = ','.join(ids[:100])
    remaining_ids = ids[100:]
    return id_string, remaining_ids

def process_ids(file_path):
    all_ids = read_ids_from_file(file_path)
    while all_ids:
        id_string, all_ids = create_id_string(all_ids)
        url = "https://www.ncbi.nlm.nih.gov/research/pubtator-api/publications/export/biocjson?pmids="
        s = requests.get(url+id_string).text.strip()

        jsons = []
        start, end = s.find('{'), s.find('}')
        while True:
            try:
                jsons.append(json.loads(s[start:end + 1]))
            except ValueError:
                end = end + 1 + s[end + 1:].find('}')
            else:
                s = s[end + 1:]
                if not s:
                    break
                start, end = s.find('{'), s.find('}')

        for JSON in jsons:
            root = ET.Element('xmi:XMI')
            root.set('xmlns:xmi', 'http://www.omg.org/XMI')
            root.set('xmlns:cas', 'http:///uima/cas.ecore')
            root.set('xmlns:type', 'http:///de/tudarmstadt/ukp/dkpro/core/api/ner/type.ecore')
            root.set('xmi:version', '2.0')

            null_element = ET.Element('cas:NULL')
            null_element.set("xmi:id","0")
            root.append(null_element)

            id=2
            name = JSON["id"]
            passages = JSON.get('passages', [])
            text = ""
            members = ""

            for passage in passages:
                text += passage.get('text', '') + " "
                annotations = passage.get('annotations', [])


                for annotation in annotations:
                    entity_id = str(id)
                    members+=(entity_id+" ")
                    start_offset = annotation['locations'][0]['offset']
                    end_offset = start_offset + annotation['locations'][0]['length']
                    label = annotation['infons'].get('type', '')
                    id+=1

                    entity_element = ET.Element('type:NamedEntity')
                    entity_element.set('xmi:id', entity_id)
                    entity_element.set('value', label)
                    entity_element.set('begin', str(start_offset))
                    entity_element.set('end', str(end_offset))
                    entity_element.set('sofa', '1')
                    root.append(entity_element)

            sofa_element = ET.Element('cas:Sofa')
            sofa_element.set('xmi:id', '1')
            sofa_element.set('sofaNum', '1')
            sofa_element.set('sofaID', '_InitialView')
            sofa_element.set('sofaString', text.strip())
            root.append(sofa_element)

            view_element = ET.Element('cas:View')
            view_element.set('sofa', '1')
            view_element.set('members', members)
            root.append(view_element)

            tree = ET.ElementTree(root)
            with open("{}_output.xmi".format(name), "wb") as outfile:
                tree.write(outfile, encoding='utf-8', xml_declaration=True)

# Enter file name
file_path = 'ids.txt'
process_ids(file_path)
