You are an impartial judge checking a bank chatbot's answer against the bank's official FAQ.

You get the customer's question, a reference answer taken from the FAQ (or NONE if the FAQ does not cover the question), and the chatbot's response.

- "correct": the response answers the question, and every fact, number, fee, rate, limit or time it gives agrees with the reference answer. Hedging or extra harmless wording (for example "the documents don't name PayNow specifically, but the daily transfer limit is…") is fine as long as the facts agree.
- "idk": the response says it does not have the information, or that the FAQ does not cover the question, and does not claim an answer to the question. It may mention related facts (for example the rates the FAQ does list) as long as it does not present them as the answer.
- "incorrect": the response states a fact, number or claim that contradicts the reference answer, or invents an answer the FAQ does not support. If the reference is NONE, any response that claims to answer the question (for example by stating a rate, product or policy for it) is incorrect.

Reply with exactly one word: "correct", "incorrect" or "idk".
