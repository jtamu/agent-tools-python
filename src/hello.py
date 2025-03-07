from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM


def main():
    model = OllamaLLM(model="llama3.1:latest", base_url="host.docker.internal:11434")

    # PROMPT
    template = """Question: {question}
    Answer: ステップバイステップで考えてみましょう。"""
    prompt = ChatPromptTemplate.from_template(template)

    # CHAIN
    chain = prompt | model
    result = chain.invoke({"question": "美味しいパスタの作り方は?"})
    print(result)


if __name__ == "__main__":
    main()
