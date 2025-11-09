print("""
To create a second tunnel for the GPU exporter (port 9400), run this in a NEW terminal:

ssh -i C:\\Users\\alpes\\.ssh\\id_ed25519 -L 19400:localhost:9400 -p 47295 root@213.173.105.12

Or using SSH config:
ssh -L 19400:localhost:9400 runpod

This will create:
localhost:19400 → runpod:9400 (GPU exporter)

Then we can test if the GPU exporter is working and has the metrics we need.
""")
