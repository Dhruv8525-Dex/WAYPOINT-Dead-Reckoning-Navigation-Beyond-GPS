import argparse
import asyncio
import uvicorn
from .api import app
from .tls import ensure_certificate

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--lan',action='store_true');args=parser.parse_args()
    async def serve():
        local=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=8000,log_level='info'))
        if args.lan:
            cert,key,fingerprint=ensure_certificate()
            print(f'Phone pairing certificate SHA256: {fingerprint}',flush=True)
            lan=uvicorn.Server(uvicorn.Config(app,host='0.0.0.0',port=8443,ssl_certfile=str(cert),ssl_keyfile=str(key),lifespan='off',log_level='info'))
            await asyncio.gather(local.serve(),lan.serve())
        else:await local.serve()
    asyncio.run(serve())
if __name__=='__main__':main()
