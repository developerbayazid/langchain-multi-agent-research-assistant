from src.agents.agents import search_agent, reader_agent, writer_chain, critic_chain
from typing import Callable


def run_research_pipeline(topic : str, progress_callback: Callable[[str, str], None] | None = None) -> dict:

    state = {}
    
    def report_progress(stage: str, message: str):
        if progress_callback:
            progress_callback(stage, message)

    #search agent working 
    print("\n"+" ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)


    # Before running the search agent
    report_progress("search", "Searching the web for reliable sources...")
    
    search_agent_instance = search_agent()
    search_result = search_agent_instance.invoke({
        "messages" : [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    state["search_results"] = search_result['messages'][-1].content

    print("\n search result ",state['search_results'])


    # Before running the reader agent
    report_progress("reader", "Reading and analyzing relevant webpages...")
    
    #step 2 - reader agent 
    print("\n"+" ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)

    # Before running the writer chain
    report_progress("writer", "Writing your research report...")
    
    reader_agent_instance = reader_agent()
    reader_result = reader_agent_instance.invoke({
        "messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}"
        )]
    })

    state['scraped_content'] = reader_result['messages'][-1].content

    print("\nscraped content: \n", state['scraped_content'])


    #step 3 - writer chain 

    print("\n"+" ="*50)
    print("step 3 - Writer is drafting the report ...")
    print("="*50)

    # Before running the writer chain
    report_progress("writer", "Writing your research report...")
    
    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic" : topic,
        "research" : research_combined
    })

    print("\n Final Report\n",state['report'])


    #critic report 

    print("\n"+" ="*50)
    print("step 4 - critic is reviewing the report ")
    print("="*50)
    
    # Before running the critic chain
    report_progress("critic", "Reviewing report quality and evidence...")

    state["feedback"] = critic_chain.invoke({
        "report":state['report']
    })

    print("\n critic report \n", state['feedback'])

    return state