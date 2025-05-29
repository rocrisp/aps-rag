import os
from pathlib import Path
from llama_stack_client import LlamaStackClient
from llama_stack_client.types import Document as LlamaStackDocument

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.types.doc.labels import DocItemLabel

def process_local_pdfs_and_store(directory_path, llamastack_base_url):
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    pdf_files = list(directory.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {directory_path}")
        return

    # Set up docling
    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)})
    chunker = HybridChunker()

    llama_documents = []
    i = 0

    for file_path in pdf_files:
        print(f"Processing {file_path}...")
        try:
            docling_doc = converter.convert(source=str(file_path)).document
            chunks = chunker.chunk(docling_doc)
            for chunk in chunks:
                if any(c.label in [DocItemLabel.TEXT, DocItemLabel.PARAGRAPH] for c in chunk.meta.doc_items):
                    i += 1
                    llama_documents.append(LlamaStackDocument(
                        document_id=f"doc-{i}",
                        content=chunk.text,
                        mime_type="text/plain",
                        metadata={"source": file_path.name},
                    ))
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"Total valid chunks prepared: {len(llama_documents)}")

    # Register and insert into vector DB
    client = LlamaStackClient(base_url=llamastack_base_url)
    try:
        client.vector_dbs.register(
            vector_db_id="test-1",
            embedding_model="all-MiniLM-L6-v2",
            embedding_dimension=384,
            provider_id="faiss",
        )
        print("Vector DB registered.")
    except Exception as e:
        print(f"DB registration skipped/failed: {e}")

    try:
        client.tool_runtime.rag_tool.insert(
            documents=llama_documents,
            vector_db_id="test-1",
            chunk_size_in_tokens=512,
        )
        print("Documents successfully inserted into vector DB.")
    except Exception as e:
        print("Insert failed:", e)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    input_dir = os.getenv("INPUT_PDF_DIR", "./pdfs")
    llamastack_url = os.getenv("LLAMASTACK_BASE_URL", "http://localhost:8321")

    process_local_pdfs_and_store(input_dir, llamastack_url)

