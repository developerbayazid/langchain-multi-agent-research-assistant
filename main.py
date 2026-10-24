from src.tools.tools import web_search, scrape_url

output = scrape_url.invoke("https://docs.langchain.com/oss/python/langchain/tools")

print(output)
