"""
Memory implementation for ATOM.
"""

# pylint: disable=line-too-long, import-error

import os
import uuid
import textwrap
from typing import List
from abc import abstractmethod
import openai
import tiktoken
import config as config


def create_ada_embedding(data: str):
    """
    Create an embedding using the OpenAI API.

    :param data: Data to create embedding for

    """
    return openai.Embedding.create(
        input=[data],
        model="text-embedding-ada-002"
    )["data"][0]["embedding"]

class Memory:
    """
    Abstract base class for various memory implementations.
    """
    def __init__(self):
        self.summarizer_model = config.SUMMARIZER_MODEL
        self.max_context_size = config.MAX_CONTEXT_SIZE
        self.summarizer_chunk_size = config.SUMMARIZER_CHUNK_SIZE

    def summarize_memory_if_large(self, memory: str, max_tokens: int, summarizer_hint = None) -> str:
        """
        Summarize a memory string if it exceeds the max_tokens limit.

        Args:
            memory (str): The memory string to be summarized.
            max_tokens (int): The maximum token limit.

        Returns:
            str: The summarized memory string.
        """
        num_tokens = len(tiktoken.encoding_for_model(
            self.summarizer_model).encode(memory))

        if num_tokens > max_tokens:
            avg_chars_per_token = len(memory) / num_tokens
            chunk_size = int(avg_chars_per_token * self.summarizer_chunk_size)
            chunks = textwrap.wrap(memory, chunk_size)
            summary_size = int(max_tokens / len(chunks))
            memory = ""

            print(f"Summarizing memory, {len(chunks)} chunks.")

            for chunk in chunks:

                messages=[
                    {"role": "user", "content": f"Shorten the following memory chunk of an autonomous agent, {summary_size} tokens max."},
                    {"role": "user", "content": f"Try to retain all semantic information including tasks performed by the agent, website content, important data points and hyper-links:\n\n{chunk}"},
                ]

                if summarizer_hint is not None:
                    messages.append(
                        {"role": "user", "content": f"If the text contains information related to the topic: '{summarizer_hint}' then include it. If not, write a standard summary."},
                    )

                response = openai.ChatCompletion.create(
                    model=self.summarizer_model,
                    messages=messages,
                )

                memory += response['choices'][0]['message']['content']

        return memory

    @abstractmethod
    def add(self, data: str):
        """
        Add a data entry to the memory.

        Args:
            data (str): The data string to be added to the memory.
        """
        raise NotImplementedError

    @abstractmethod
    def get_context(self, data, num=5):
        """
        Retrieve context data from the memory based on a query.

        Args:
            data: The query data.
            num (int, optional): The number of memory items to retrieve. Defaults to 5.

        Returns:
            str: The retrieved context.
        """
        raise NotImplementedError


memory_type = config.MEMORY_TYPE

if memory_type == "pinecone":
    import pinecone

    class PineconeMemory(Memory):
        """
        Pinecone memory implementation.
        """
        def __init__(self):
            super().__init__()
            pinecone.init(
                api_key=config.PINECONE_API_KEY,
                environment=config.PINECONE_ENVIRONMENT
            )

            if "atom" not in pinecone.list_indexes():
                print("Creating Pinecode index...")
                pinecone.create_index(
                    "atom", dimension=1536, metric="cosine", pod_type="p1"
                )

            self.index = pinecone.Index("atom")

            if config.CLEAR_DB_ON_START in ['true', '1', 't', 'y', 'yes']:
                self.index.delete(deleteAll='true')

        def add(self, data: str):
            """
            Add a data entry to the Pinecone memory.

            Args:
                data (str): The data string to be added to the memory.
            """
            vector = create_ada_embedding(data)

            _id = uuid.uuid1()

            self.index.upsert([(str(_id), vector, {"data": data})])

        def get_context(self, data, num=5):
            """
            Retrieve context data from the Pinecone memory based on a query.

            Args:
                data: The query data.
                num (int, optional): The number of memory items to retrieve. Defaults to 5.

            Returns:
                str: The retrieved context.
            """
            vector = create_ada_embedding(data)
            results = self.index.query(
                vector, top_k=num, include_metadata=True
            )
            sorted_results = sorted(results.matches, key=lambda x: x.score)
            results_list = [str(item["metadata"]["data"])
                            for item in sorted_results]
            context = "\n".join(results_list)

            context = self.summarize_memory_if_large(
                context, self.max_context_size)

            return context


else:
    raise ValueError("Invalid MEMORY_TYPE environment variable")


def get_memory_instance():
    """
    Return the memory implementation based on memory_type
    """
    if memory_type == "pinecone":
        return PineconeMemory()

    raise ValueError("Invalid MEMORY_TYPE environment variable")