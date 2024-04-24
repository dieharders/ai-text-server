from llama_index.core.evaluation.faithfulness import FaithfulnessEvaluator


# Determine which nodes contributed to the answer
def contributing_references(response, eval_result):
    num_source_nodes = len(response.source_nodes)
    print(f"[embedding api] Number of source nodes: {num_source_nodes}", flush=True)
    print(f"[embedding api] Result is passing? {str(eval_result.passing)}", flush=True)
    for s in response.source_nodes:
        print(f"[embedding api] Node Score: {s.score}", flush=True)
        print(s.node.metadata, flush=True)
    return {
        "num_refs": num_source_nodes,
    }


# Verifies whether a response is faithful to the contexts
# @TODO Needs refactor for llama-index 0.10.0
def verify_response(response, query=""):
    print("[embedding api] Verifying truthiness of response...", flush=True)
    evaluator = FaithfulnessEvaluator()
    eval_result = evaluator.evaluate_response(query=query, response=response)
    print(f"[embedding api] Faithfulness results: {eval_result}", flush=True)
    contributing_references(response, eval_result)


# Evaluates whether a response is faithful to the query
# @TODO Needs refactor for llama-index 0.10.0
def evaluate_response(response, query=""):
    # Define evaluator, evaluates whether a response is faithful to the contexts
    print("[embedding api] Evaluating correctness of response...", flush=True)
    evaluator = FaithfulnessEvaluator()
    eval_result = evaluator.evaluate(
        query=query,
        response=response,
    )
    print(f"[embedding api] Verification results: {eval_result}", flush=True)
    contributing_references(response, eval_result)
