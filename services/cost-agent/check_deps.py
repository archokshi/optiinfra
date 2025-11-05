"""Check if all dependencies are installed"""
import requests
import aiohttp
import tenacity
import responses

print('✅ requests:', requests.__version__)
print('✅ aiohttp:', aiohttp.__version__)
print('✅ tenacity: imported successfully')
print('✅ responses: imported successfully')
print('\n✅ All dependencies installed!')
