import openai


class Gpt3:
    @staticmethod
    def set_api_key(key: str):
        openai.api_key = key

    @staticmethod
    def ask(question: str, model="text-davinci-003", temperature=0.15, max_tokens=256, top_p=1,
            frequency_penalty=0, presence_penalty=0):
        response = openai.Completion.create(
            model=model,
            prompt=question,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        answer = response.to_dict()["choices"][0]["text"]
        return answer.strip().strip('""')  # remove quotes
