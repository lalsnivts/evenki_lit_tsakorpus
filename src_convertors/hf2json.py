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

    def convert(self):
        tStart = time.time()
        if not os.path.exists(self.src_file):
            print(f"File not found: {self.src_file}")
            return

        os.makedirs(self.target_dir, exist_ok=True)
        
        all_sentences = []
        
        print(f"Starting processing of {self.src_file}...")
        
        with open(self.src_file, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                processed_evn_sents, _, _, _ = self.tp.process_string(item["evn"])
                processed_rus_sents, _, _, _ = self.tp.process_string(item["ru"])
                para_id = len(all_sentences) + 1
        
                for s in processed_evn_sents:
                    s['lang'] = 0
                    s['para_alignment'] = [{'para_id': para_id}]
                    if 'meta' not in s:
                        s['meta'] = {}
                    s['meta']['source'] = item.get('source', '')
                    all_sentences.append(s)

                for s in processed_rus_sents:
                    s['lang'] = 1
                    s['para_alignment'] = [{'para_id': para_id}]
                    if 'meta' not in s:
                        s['meta'] = {}
                    s['meta']['source'] = item.get('source', '')
                    all_sentences.append(s)

        final_json = {
            'meta': {'title': 'Evenki HF Dataset', 'filename': 'evenki_data.json'},
            'sentences': all_sentences
        }

        output_fname = os.path.join(self.target_dir, 'evenki_data.json')
        with open(output_fname, 'w', encoding='utf-8') as f_out:
            json.dump(final_json, f_out, ensure_ascii=False, indent=self.corpusSettings.get('json_indent', 2))
            
        print(f"Processed in {time.time() - tStart:.2f} seconds.")
        print(f"Result saved to: {output_fname}")

if __name__ == '__main__':
    converter = HF2JSON()
    converter.convert()