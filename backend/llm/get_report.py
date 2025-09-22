from langchain_groq import ChatGroq
from langchain_community.output_parsers import StrOutputParser, StructuredOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional, Annotated, Dict, Any

from backend.llm.get_api import load_apikey

groq_api_key = load_apikey()


class ReportStructure(BaseModel):
    title: str = Field(..., description="The title of the report")
    detailed_summary: str = Field(..., description="A detailed summary of the report in at least 500 words")
    links: Annotated[Dict[str, str], Field(..., description="A dictionary of urls used to generate report")]


class ReportGenerator(BaseModel):
    '''
       ReportGenerator class is used to generate summaries of the parsed data from urls.

       Attributes:

    '''
    api_key = groq_api_key
    
    async def _get_chain(self, data: Dict[str, Any], temperature = 0.2):
        if not groq_api_key:
            raise ValueError('GROQ_API_KEY enironment variable is not set. Please set it first to generate report.')
        
        groq = ChatGroq(model= "llama-3.3-70b-versatile",
                        api_key= self.api_key,
                        temperature= temperature)
        SYSTEM_PROMPT = f'''
            You are an expert in report generation. Generate a concise and informative report based on the provided
            Researched Data.

            The report should include bullet points if needed. Ensure clarity and coherence in the summary.
            Use the following format:
            Title: <Title of the Report>
            Detailed Summary (in 500 words atleast)

            Examples:
                Title: The Impact of Climate Change in Coastal Regions
                Detailed Summary: .....
                Links: {{
                    'url link': 'Link Accessed',
                    'url link': Reason why access failed
                }}

                Title: Advances in Artificial Intelligence and Machine Learning
                Detailed Summary: .....
                Links: {{
                    'url link': 'Link Accessed',
                    'url link': Reason why access failed
                }}

            Researched Data : {data}
            Report: <Report>
        '''
        prompt = PromptTemplate(template = SYSTEM_PROMPT,
                                input_variables = ['data'])

        chain = prompt | groq | StructuredOutputParser.from_model(ReportStructure)
        return chain


    async def generate_report(self, data: Dict[str, Any], temperature = 0.2) -> Dict[str, str]:
        '''
        Generate a summarized report from the provided data.
        
        Args:
            data: The data that is extracted from tools(web_search tool, content_extractor tool).
            temperatur: default = 0.2
        
        Returns:
        '''
        try:
            chain = await self._get_chain(data=data, temperature=temperature)

            response = chain.ainvoke({
                'data': data
            })
            if response:
                return response
            else:
                return {'error': 'Failed to generate report'}
        except Exception as e:
            return {"error": str(e)}
        
        
        
        

