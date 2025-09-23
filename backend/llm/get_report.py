from langchain_groq import ChatGroq
from langchain_core.output_parsers import PydanticOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional, Annotated, Dict, Any, ClassVar
import re

from backend.llm.get_api import load_apikey

groq_api_key = load_apikey()


class ReportStructure(BaseModel):
    title: str = Field(..., description="The title of the report")
    detailed_summary: str = Field(..., description="A detailed summary of the report in 500 to 800 words")
    links: Dict[str, str] = Field(default_factory=dict, description="A dictionary of urls used to generate report")


class ReportGenerator(BaseModel):
    '''
       ReportGenerator class is used to generate summaries of the parsed data from urls.

       Attributes:

    '''
    api_key: ClassVar[str] = groq_api_key

    @staticmethod
    async def _chunk_data(data: Dict[str, Any], chunk_size: int = 6000, chunk_overlap: int = 300) -> List[str]:
        """
        Splits the extracted contents dictionary into smaller text chunks.

        Args:
            data: Dictionary with urls -> {"text": "...", "source": "..."}
            chunk_size: Max chunk size in characters (approx tokens).
            chunk_overlap: Overlap between chunks.

        Returns:
            List[str]: List of text chunks.
        """
        def clean_text(text: str) -> str:
            # Keep normal punctuation for coherence; only strip weird control characters
            return re.sub(r'[^\x00-\x7F]+', ' ', text)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

        print('Combining data into one big string...')
        all_texts = []
        for url, content in data.items():
            if isinstance(content, dict) and "text" in content:
                all_texts.append(clean_text(content["text"]))
            elif isinstance(content, str):
                all_texts.append(clean_text(content))

        combined_text = "\n\n".join(all_texts)
        print('Data combined.')

        return text_splitter.split_text(combined_text)

    async def _get_chain(self, temperature = 0.2):
        if not groq_api_key:
            raise ValueError('GROQ_API_KEY enironment variable is not set. Please set it first to generate report.')
        
        groq = ChatGroq(model= "llama-3.1-8b-instant",
                        api_key= self.api_key,
                        temperature= temperature)
        
        parser = PydanticOutputParser(pydantic_object=ReportStructure)

        SYSTEM_PROMPT = '''
            You are an expert in report generation. Generate a concise and informative report based on the provided
            Researched Data.

            The report should include bullet points if needed. Ensure clarity and coherence in the summary.
            Use the following format:
            title: <Title of the Report>
            detailed_summary (in 500 to 800 words atleast)
            links: dictionary of links {{url link: access denied/rejected with reason}}

            Examples:
                title: The Impact of Climate Change in Coastal Regions
                detailed_summary: .....
                links: {{
                    'url link': 'Link Accessed',
                    'url link': Reason why access failed
                }}

                title: Advances in Artificial Intelligence and Machine Learning
                detailed_summary: .....
                links: {{
                    'url link': 'Link Accessed',
                    'url link': Reason why access failed
                }}

            Instructions : {instructions}

            Researched Data : {data}
            Report: <Report>
        '''
        prompt = PromptTemplate(template = SYSTEM_PROMPT,
                                input_variables = ['instructions', 'data'])

        # parser = StructuredOuputParser.from_response_schema()
        chain = prompt | groq | parser
        return chain


    async def _get_condensation_chain(self, temperature=0.2):
        """A separate chain for creating more concise summaries during re-summarization."""
        if not groq_api_key:
            raise ValueError('GROQ_API_KEY environment variable is not set.')

        groq = ChatGroq(model="llama-3.1-8b-instant", api_key=self.api_key, temperature=temperature)

        CONDENSATION_PROMPT = '''
            You are an expert in text summarization. Your task is to take the following text
            and create a concise, condensed summary of it. The goal is to reduce the overall length
            while preserving the key information.

            Do not add any extra information, titles, or formatting. Only return the summarized text.

            Original Text: {data}
            Condensed Summary:
        '''
        prompt = PromptTemplate(template=CONDENSATION_PROMPT, input_variables=['data'])

        chain = prompt | groq
        return chain


    async def generate_report(self, data: Dict[str, Any], temperature = 0.2) -> Dict[str, str]:
        '''
        Generate a summarized report from the provided data.
        
        Args:
            data: The data that is extracted from tools(web_search tool, content_extractor tool).
            temperatur: default = 0.2
        
        Returns:
            Dict[str, str]: A dictionary containing:
                - title: The generated report title
                - detailed_summary: A 500 to 800 word summary
                - links: Dictionary of processed URLs and their status
                - error: Error message if generation fails
        
        Raises:
            ValueError: If API key is missing or invalid
            Exception: For other unexpected errors during report generation
        '''
        try:
            # 1. Initial chunking and summarization
            chunks = await self._chunk_data(data['extracted_contents'])
            print(f"Total chunks to summarize: {len(chunks)}")

            partial_summaries = []
            for i, chunk in enumerate(chunks, 1):
                chain = await self._get_chain(temperature=temperature)
                try:
                    response: ReportStructure = await chain.ainvoke({
                        "data": {"chunk_text": chunk},
                        "instructions": PydanticOutputParser(pydantic_object=ReportStructure).get_format_instructions()
                    })
                    partial_summaries.append(response.detailed_summary)
                    print(f"✔️ Finished chunk {i}/{len(chunks)}")
                except Exception as chunk_error:
                    print(f"⚠️ Error processing chunk {i}: {chunk_error}")
                    # Optionally skip this chunk or handle the error in another way
                    continue

            # 2. Iteratively summarize until the content is small enough
            combined_summary = "\n\n".join(partial_summaries)
            # Define a max length, e.g., based on the chunk size
            max_len = 6000

          
            while len(combined_summary) > max_len:
                print(f"Combined summary is too long ({len(combined_summary)} chars). Summarizing further...")
                # Create a new set of chunks from the oversized summary
                new_chunks = await self._chunk_data({"combined": {"text": combined_summary}})
                partial_summaries = [] # Reset for the new, more condensed summaries

                for i, chunk in enumerate(new_chunks, 1):
                    # Use the condensation chain for re-summarization
                    chain = await self._get_condensation_chain(temperature=temperature)
                    try:
                        # The condensation chain returns a string directly
                        response = await chain.ainvoke({"data": chunk})
                        # Assuming the response object has a 'content' attribute with the text
                        partial_summaries.append(response.content)
                        print(f"✔️ Finished re-summarizing chunk {i}/{len(new_chunks)}")
                    except Exception as chunk_error:
                        print(f"⚠️ Error processing re-summary chunk {i}: {chunk_error}")
                        continue
                
                combined_summary = "\n\n".join(partial_summaries)

            # 3. Generate the final report from the condensed summary
            print("Generating final report...")
            chain = await self._get_chain(temperature=temperature)
            final_report: ReportStructure = await chain.ainvoke({
                "data": {"final_summary": combined_summary},
                "instructions": PydanticOutputParser(pydantic_object=ReportStructure).get_format_instructions()
            })

            return final_report.model_dump()

        except ValueError as ve:
            return {"error": f"API Error: {str(ve)}"}
        except Exception as e:
            return {"error": str(e)}
