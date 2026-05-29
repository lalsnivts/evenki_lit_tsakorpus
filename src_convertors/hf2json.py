import os
import json
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'simple_convertors'))
from simple_convertors.text_processor import TextProcessor

class HF2JSON:
    def __init__(self):
        conv_settings_dir = os.path.join(os.path.dirname(__file__), 'conf_conversion')
        root_conf_dir = os.path.join(os.path.dirname(__file__), '..', 'conf')
        
        with open(os.path.join(conv_settings_dir, 'conversion_settings.json'), 'r', encoding='utf-8') as f:
            self.corpusSettings = json.load(f)
        
        with open(os.path.join(root_conf_dir, 'categories.json'), 'r', encoding='utf-8') as f:
            self.categories = json.load(f)

        self.tp = TextProcessor(settings=self.corpusSettings,
                                categories=self.categories)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))

        self.src_file = os.path.join(base_dir, '..', 'data_raw', 'evenki_data.json')
        self.src_file = os.path.abspath(self.src_file)

        self.target_dir = os.path.join(base_dir, '..', 'corpus', 'evenki', self.corpusSettings['corpus_name'])
        self.target_dir = os.path.abspath(self.target_dir)

    def _clean_value(self, val, field_name):
        if val is None:
            return ""
        v_str = str(val).strip()
        if v_str.lower() == 'nan' or v_str == '':
            return ""
        if field_name == 'year_of_publication' and isinstance(val, float):
            return str(int(val))
        return v_str

    def convert(self):
        tStart = time.time()
        if not os.path.exists(self.src_file):
            print(f"File not found: {self.src_file}")
            return

        os.makedirs(self.target_dir, exist_ok=True)
        
        print(f"Starting processing of {self.src_file}...")
        
        documents = {}
        doc_meta_fields = ['title', 'author', 'translator', 'year_of_publication', 'genre', 'type', 'source_language']

        with open(self.src_file, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                source = item.get('source')
                if not source:
                    continue
                
                # ИЗМЕНЕНИЕ: Заводим два раздельных списка под языки
                if source not in documents:
                    documents[source] = {
                        'meta': {
                            'filename': source,
                            'title': '', 'author': '', 'translator': '', 
                            'year_of_publication': '', 'genre': '', 
                            'type': '', 'source_language': ''
                        },
                        'sentences_evn': [],
                        'sentences_ru': [],
                        'para_count': 0
                    }
                
                doc_meta = documents[source]['meta']
                for field in doc_meta_fields:
                    if not doc_meta[field]:
                        val = self._clean_value(item.get(field), field)
                        if val:
                            doc_meta[field] = val.replace('\n', ' ')

                documents[source]['para_count'] += 1
                para_id = documents[source]['para_count']
                
                processed_evn_sents, _, _, _ = self.tp.process_string(item.get("evn", ""))
                processed_rus_sents, _, _, _ = self.tp.process_string(item.get("ru", ""))
                
                sent_num = item.get('sentence_num')
                internal_id = item.get('internal_id')
                
                # Заполняем эвенкийский список
                for s in processed_evn_sents:
                    s['lang'] = 0
                    s['para_alignment'] = [{'para_id': str(para_id)}]
                    if 'meta' not in s:
                        s['meta'] = {}
                    
                    s['meta']['source'] = source 
                    
                    if sent_num is not None: s['meta']['sentence_num'] = sent_num
                    if internal_id is not None: s['meta']['internal_id'] = internal_id
                    
                    documents[source]['sentences_evn'].append(s)

                # Заполняем русский список
                for s in processed_rus_sents:
                    s['lang'] = 1
                    s['para_alignment'] = [{'para_id': str(para_id)}]
                    if 'meta' not in s:
                        s['meta'] = {}
                        
                    s['meta']['source'] = source
                    
                    if sent_num is not None: s['meta']['sentence_num'] = sent_num
                    if internal_id is not None: s['meta']['internal_id'] = internal_id
                    
                    documents[source]['sentences_ru'].append(s)

        for source, doc_data in documents.items():
            # ИЗМЕНЕНИЕ: Склеиваем массивы: сначала все эвенкийские, потом все русские
            final_json = {
                'meta': doc_data['meta'],
                'sentences': doc_data['sentences_evn'] + doc_data['sentences_ru']
            }
            safe_filename = "".join([c for c in source if c.isalpha() or c.isdigit() or c in ['_', '-']]).rstrip()
            if not safe_filename:
                safe_filename = "document"
                
            output_fname = os.path.join(self.target_dir, f"{safe_filename}.json")
            with open(output_fname, 'w', encoding='utf-8') as f_out:
                json.dump(final_json, f_out, ensure_ascii=False, indent=self.corpusSettings.get('json_indent', 2))
            
        print(f"Processed in {time.time() - tStart:.2f} seconds.")
        print(f"Total documents generated: {len(documents)}")

if __name__ == '__main__':
    converter = HF2JSON()
    converter.convert()