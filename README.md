# Crypto Yield Optimizing Cloud Pipeline

### Overview

A decentralized finance (DeFi) platform integrated with a scalable cloud backend that enables users to earn passive income by supplying assets to lending protocols like Aave and Compound. The system automates yield optimization using event-driven pipelines, live on-chain monitoring, and real-time reallocation logic.

### Authors and Contribution
Sreynit Khatt – Computer Science, sreynit.khatt@vanderbilt.edu - dockerfiles, yaml files, VMs, k8s pod set up, CouchDB setup
Hanlin Chen – Data Science Institute, hanlin.chen@vanderbilt.edu - prediction, API producer, consumer
Hannah Wang – Computer Science, hannah.a.wang@vanderbilt.edu - onchain (contracts, backend and protocol operators), frontend ~80%
DeAnthony L. Dixon – Computer Science, deanthony.l.dixon@vanderbilt.edu - frontend ~20%

### Features

- Smart Contract Vault: Securely holds user funds and triggers backend workflows on deposit/withdraw events.
- Automatic Rebalancing: Cloud-based backend reallocates funds to maximize yield based on real-time DefiLlama data.
- Scalable Cloud Stack: Powered by VMs, Docker, Kubernetes, CouchDB, and Kafka.
- Prediction and Recommendation: predicts returns and confidence levels for each protocol-token pair to deliver personalized, real-time DeFi investment suggestions based on user-selected profiles.
- React Dashboard: Users can connect wallets, view live yields, monitor deposits, and withdraw with one click.

### Architecture

Frontend (React + Infura):
    - Connects to MetaMask.
    - Shows current protocol, APY, token type, and vault balance.
    - Allows ETH deposit and smart contract interaction.

Backend (Python):
    - Listens to CouchDB changes triggered by smart contract events.
    - Executes rebalancing logic via get_protocol_operator abstraction.
    - Fetches and processes yield data every 10 minutes from DeFi APIs.

Smart Contract (Solidity):
    - Handles deposit, depositToken, getBalance, withdrawToProtocol.
    - Emits events that trigger cloud-based workflows.

Infrastructure:
    - Kafka & Zookeeper: Real-time messaging.
    - CouchDB: Strategy and yield data storage.
    - Ansible + Docker + Kubernetes: Scalable deployment and orchestration.


### Quickstart
- Install metamask https://metamask.io/download

```
# Clone repository
git clone https://github.com/hanlin123456666/crypto-yield-optimizer.git
cd crypto-yield-optimizer

# Run frontend (React)
cd frontend
npm install
npm run dev
```

### Technologies
    - Ethereum (Sepolia Testnet)
    - Solidity Smart Contracts + Foundry
    - React + Web3.js + Infura
    - Python + Web3.py + Requests
    - Kafka + Zookeeper + CouchDB
    - Kubernetes + Docker + Ansible

### Future Integrations
- Advanced Yield Prediction Models: more sophisticated, customized yield prediction model that integrates a wider range of financial indicators and blockchain-specific metrics.
- Diversification of Investment Options: include a broader selection of investment types ranging from staking and liquidity provision to algorithmic yield strategies. 
- Support for Additional Chains: prioritize integration with Layer 2 (L2) scaling solutions such as Arbitrum, Optimism, and Base. These L2s offer significantly lower transaction costs
and faster confirmation times, making them ideal for more frequent rebalancing and user interactions.
- Integration with Additional Lending Protocols: expand to include more DeFI protocols like Lido and Morpho in addition to Aave and Compound
- User Personalization and Insights: provide users with actionable insights into their investment performance, along with recommendations based on historical behavior and market trends.
