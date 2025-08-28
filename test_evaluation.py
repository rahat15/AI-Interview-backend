from cv_eval.engine import CVEvaluationEngine

def main():
    with open("samples/sample_cv.txt") as f:
        cv_text = f.read()
    with open("samples/sample_jd.txt") as f:
        jd_text = f.read()

    engine = CVEvaluationEngine(use_llm=True)
    result = engine.evaluate(cv_text, jd_text)

    print("🔍 Raw JSON result from LLM:")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
