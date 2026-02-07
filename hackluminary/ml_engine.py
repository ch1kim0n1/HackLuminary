import torch
from transformers import pipeline

class MLEngine:
    """AI engine for enhancing hackathon presentations."""
    
    def __init__(self):
        print("🧠 Initializing Neural Engine...")
        # Use a lightweight model for speed and low memory usage
        # LaMini-Flan-T5-248M is excellent for instruction following and summarization
        model_id = "MBZUAI/LaMini-Flan-T5-248M"
        
        device = 0 if torch.cuda.is_available() else -1
        
        try:
            self.generator = pipeline(
                "text2text-generation",
                model=model_id,
                device=device,
                max_length=512
            )
        except Exception as e:
            print(f"⚠ Warning: Failed to load AI model: {e}")
            self.generator = None

    def enhance_docs(self, doc_data, code_analysis):
        """Enhance documentation data with AI-generated content."""
        if not self.generator:
            return doc_data

        print("✨ Enhancing presentation content with AI...")
        
        project_name = doc_data.get('title', 'Project')
        primary_lang = code_analysis.get('primary_language', 'Code')
        
        # Context building
        context = f"Project: {project_name}\nLanguage: {primary_lang}\n"
        if doc_data.get('description'):
            context += f"Description: {doc_data['description']}\n"
        
        # 1. Enhance/Generate Problem Statement
        if not doc_data.get('problem') or len(doc_data['problem']) < 50:
            print("  - Genering problem statement...")
            prompt = f"{context}\nWrite a compelling 2-sentence 'Problem Statement' that this hackathon project solves.\nProblem:"
            doc_data['problem'] = self._generate(prompt)

        # 2. Enhance/Generate Solution
        if not doc_data.get('solution') or len(doc_data['solution']) < 50:
            print("  - Genering solution description...")
            prompt = f"{context}\nProblem: {doc_data.get('problem')}\nWrite a persuasive 2-sentence 'Solution' description for this project.\nSolution:"
            doc_data['solution'] = self._generate(prompt)

        # 3. Generate Impact
        if 'impact' not in doc_data: # Custom key for ML engine
            print("  - Genering impact points...")
            prompt = f"{context}\nList 3 key benefits/impacts of this project. Format as a comma-separated list.\nImpacts:"
            impact_text = self._generate(prompt)
            doc_data['impact_points'] = [x.strip() for x in impact_text.split(',')]

        return doc_data

    def _generate(self, prompt, max_new_tokens=100):
        try:
            output = self.generator(prompt, max_new_tokens=max_new_tokens, do_sample=True, temperature=0.7)
            return output[0]['generated_text']
        except Exception:
            return ""
