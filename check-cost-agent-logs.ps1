docker logs optiinfra-cost-agent --tail 50 2>&1 | Select-String "cost|error|warning|Total"
