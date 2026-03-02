import asyncio
import json
import os
from collections import defaultdict

import agentops  # type: ignore[reportMissingImports]
import colorama  # type: ignore[reportMissingImports]
import ollama  # type: ignore[reportMissingImports]
import weave  # type: ignore[reportMissingImports]
import anthropic  # type: ignore[reportMissingImports]
from llama_index.core import Document, SimpleDirectoryReader  # type: ignore[reportMissingImports]
from llama_index.core.schema import ImageDocument  # type: ignore[reportMissingImports]
from llama_index.core.node_parser import TokenTextSplitter  # type: ignore[reportMissingImports]
from termcolor import colored  # type: ignore[reportMissingImports]


# 移除 agentops 装饰器（API 不兼容）
async def get_dir_summaries(path: str):
    doc_dicts = load_documents(path)
    # metadata = process_metadata(doc_dicts)

    summaries = await get_summaries(doc_dicts)

    # Convert path to relative path
    for summary in summaries:
        summary["file_path"] = os.path.relpath(summary["file_path"], path)

    return summaries

    # [
    #     {
    #         file_path:
    #         file_name:
    #         file_size:
    #         content:
    #         summary:
    #         creation_date:
    #         last_modified_date:
    #     }
    # ]



def load_documents(path: str):
    reader = SimpleDirectoryReader(
        input_dir=path,
        recursive=True,
        required_exts=[
            ".pdf",
            # ".docx",
            # ".py",
            ".txt",
            # ".md",
            ".png",
            ".jpg",
            ".jpeg",
            # ".ts",
        ],
    )
    splitter = TokenTextSplitter(chunk_size=6144)
    documents = []
    for docs in reader.iter_data():
        # By default, llama index split files into multiple "documents"
        if len(docs) > 1:
            # So we first join all the document contexts, then truncate by token count
            for d in docs:
                # Some files will not have text and need to be handled
                contents = splitter.split_text("\n".join(d.text))
                if len(contents) > 0:
                    text = contents[0]
                else:
                    text = ""
                documents.append(Document(text=text, metadata=docs[0].metadata))
        else:
            documents.append(docs[0])
    return documents



def process_metadata(doc_dicts):
    file_seen = set()
    metadata_list = []
    for doc in doc_dicts:
        if doc["file_path"] not in file_seen:
            file_seen.add(doc["file_path"])
            metadata_list.append(doc)
    return metadata_list


def create_anthropic_client():
    base_url = os.environ.get("OPENAI_BASE_URL", "").rstrip("/")
    return anthropic.Anthropic(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=base_url,
        default_headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    )


async def summarize_document(doc, client):
    PROMPT = """
You will be provided with the contents of a file along with its metadata. Provide a summary of the contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

Write your response a JSON object with the following schema:

```json
{
    "file_path": "path to the file including name",
    "summary": "summary of the content"
}
```
""".strip()

    max_retries = 5
    attempt = 0
    chat_completion = None
    while attempt < max_retries:
        try:
            chat_completion = client.messages.create(
                model=os.environ.get("OPENAI_MODEL", "claude-haiku-4-5-20251001"),
                max_tokens=4096,
                system=PROMPT,
                messages=[{"role": "user", "content": json.dumps(doc)}],
            )
            break
        except Exception as e:
            print("Error status {}".format(getattr(e, "status_code", "unknown")))
            attempt += 1

    if chat_completion is None:
        raise RuntimeError("Failed to summarize document after retries")

    summary = json.loads(chat_completion.content[0].text)

    try:
        # Print the filename in green
        print(colored(summary["file_path"], "green"))
        print(summary["summary"])  # Print the summary of the contents
        # Print a separator line with spacing for readability
        print("-" * 80 + "\n")
    except KeyError as e:
        print(e)
        print(summary)

    return summary


async def summarize_image_document(doc: ImageDocument, client):
    PROMPT = """
You will be provided with an image along with its metadata. Provide a summary of the image contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

Write your response a JSON object with the following schema:

```json
{
    "file_path": "path to the file including name",
    "summary": "summary of the content"
}
```
""".strip()

    import base64
    if not doc.image_path:
        raise ValueError("Image path is missing")
    with open(doc.image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    chat_completion = client.messages.create(
        model=os.environ.get("OPENAI_MODEL", "claude-haiku-4-5-20251001"),
        max_tokens=128,
        system="Return only one concise sentence for file organization purposes.",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Summarize the contents of this image in one concise sentence for file organization purposes."},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image,
                        },
                    },
                ],
            }
        ],
    )

    summary = {
        "file_path": doc.image_path,
        "summary": chat_completion.content[0].text,
    }

    # Print the filename in green
    print(colored(summary["file_path"], "green"))
    print(summary["summary"])  # Print the summary of the contents
    # Print a separator line with spacing for readability
    print("-" * 80 + "\n")
    return summary


async def dispatch_summarize_document(doc, client):
    if isinstance(doc, ImageDocument):
        return await summarize_image_document(doc, client)
    elif isinstance(doc, Document):
        return await summarize_document({"content": doc.text, **doc.metadata}, client)
    else:
        raise ValueError("Document type not supported")


async def get_summaries(documents):
    client = create_anthropic_client()
    summaries = await asyncio.gather(
        *[dispatch_summarize_document(doc, client) for doc in documents]
    )
    return summaries



def merge_summary_documents(summaries, metadata_list):
    list_summaries = defaultdict(list)

    for item in summaries:
        list_summaries[item["file_path"]].append(item["summary"])

    file_summaries = {
        path: ". ".join(summaries) for path, summaries in list_summaries.items()
    }

    file_list = [
        {"summary": file_summaries[file["file_path"]], **file} for file in metadata_list
    ]

    return file_list


################################################################################################
# Non-async versions of the functions                                                        #
################################################################################################


def get_file_summary(path: str):
    client = create_anthropic_client()
    reader = SimpleDirectoryReader(input_files=[path]).iter_data()

    docs = next(reader)
    splitter = TokenTextSplitter(chunk_size=6144)
    text = splitter.split_text("\n".join([d.text for d in docs]))[0]
    doc = Document(text=text, metadata=docs[0].metadata)
    summary = dispatch_summarize_document_sync(doc, client)
    return summary


def dispatch_summarize_document_sync(doc, client):
    if isinstance(doc, ImageDocument):
        return summarize_image_document_sync(doc, client)
    elif isinstance(doc, Document):
        return summarize_document_sync({"content": doc.text, **doc.metadata}, client)
    else:
        raise ValueError("Document type not supported")


def summarize_document_sync(doc, client):
    PROMPT = """
You will be provided with the contents of a file along with its metadata. Provide a summary of the contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

Write your response a JSON object with the following schema:
    
```json 
{
    "file_path": "path to the file including name",
    "summary": "summary of the content"
}
```
""".strip()

    chat_completion = client.messages.create(
        model=os.environ.get("OPENAI_MODEL", "claude-haiku-4-5-20251001"),
        max_tokens=4096,
        system=PROMPT,
        messages=[{"role": "user", "content": json.dumps(doc)}],
    )
    summary = json.loads(chat_completion.content[0].text)

    try:
        # Print the filename in green
        print(colored(summary["file_path"], "green"))
        print(summary["summary"])  # Print the summary of the contents
        # Print a separator line with spacing for readability
        print("-" * 80 + "\n")
    except KeyError as e:
        print(e)
        print(summary)

    return summary


def summarize_image_document_sync(doc: ImageDocument, client):
    import base64
    if not doc.image_path:
        raise ValueError("Image path is missing")
    with open(doc.image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    chat_completion = client.messages.create(
        model=os.environ.get("OPENAI_MODEL", "claude-haiku-4-5-20251001"),
        max_tokens=128,
        system="Return only one concise sentence for file organization purposes.",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Summarize the contents of this image in one concise sentence for file organization purposes."},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image,
                        },
                    },
                ],
            }
        ],
    )

    summary = {
        "file_path": doc.image_path,
        "summary": chat_completion.content[0].text,
    }

    # Print the filename in green
    print(colored(summary["file_path"], "green"))
    print(summary["summary"])  # Print the summary of the contents
    # Print a separator line with spacing for readability
    print("-" * 80 + "\n")

    return summary
