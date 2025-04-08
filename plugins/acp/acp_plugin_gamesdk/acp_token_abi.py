ACP_TOKEN_ABI = [
    {"inputs": [], "stateMutability": "nonpayable", "type": "constructor"},
    {"inputs": [], "name": "AccessControlBadConfirmation", "type": "error"},
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"},
            {"internalType": "bytes32", "name": "neededRole", "type": "bytes32"},
        ],
        "name": "AccessControlUnauthorizedAccount",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "address", "name": "target", "type": "address"}],
        "name": "AddressEmptyCode",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "AddressInsufficientBalance",
        "type": "error",
    },
    {"inputs": [], "name": "FailedInnerCall", "type": "error"},
    {"inputs": [], "name": "InvalidInitialization", "type": "error"},
    {"inputs": [], "name": "NotInitializing", "type": "error"},
    {"inputs": [], "name": "ReentrancyGuardReentrantCall", "type": "error"},
    {
        "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
        "name": "SafeERC20FailedOperation",
        "type": "error",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "jobId",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "newBudget",
                "type": "uint256",
            },
        ],
        "name": "BudgetSet",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "jobId",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "evaluator",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "evaluatorFee",
                "type": "uint256",
            },
        ],
        "name": "ClaimedEvaluatorFee",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "jobId",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "provider",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "providerFee",
                "type": "uint256",
            },
        ],
        "name": "ClaimedProviderFee",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint64",
                "name": "version",
                "type": "uint64",
            },
        ],
        "name": "Initialized",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "jobId",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "client",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "provider",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "evaluator",
                "type": "address",
            },
        ],
        "name": "JobCreated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "jobId",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint8",
                "name": "oldPhase",
                "type": "uint8",
            },
            {"indexed": False, "internalType": "uint8", "name": "phase", "type": "uint8"},
        ],
        "name": "JobPhaseUpdated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "memoId",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "bool",
                "name": "isApproved",
                "type": "bool",
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "reason",
                "type": "string",
            },
        ],
        "name": "MemoSigned",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "jobId",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "sender",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "memoId",
                "type": "uint256",
            },
        ],
        "name": "NewMemo",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "jobId",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "client",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256",
            },
        ],
        "name": "RefundedBudget",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "role", "type": "bytes32"},
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "previousAdminRole",
                "type": "bytes32",
            },
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "newAdminRole",
                "type": "bytes32",
            },
        ],
        "name": "RoleAdminChanged",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "role", "type": "bytes32"},
            {
                "indexed": True,
                "internalType": "address",
                "name": "account",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "sender",
                "type": "address",
            },
        ],
        "name": "RoleGranted",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "role", "type": "bytes32"},
            {
                "indexed": True,
                "internalType": "address",
                "name": "account",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "sender",
                "type": "address",
            },
        ],
        "name": "RoleRevoked",
        "type": "event",
    },
    {
        "inputs": [],
        "name": "ADMIN_ROLE",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "DEFAULT_ADMIN_ROLE",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "PHASE_COMPLETED",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "PHASE_EVALUATION",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "PHASE_NEGOTIATION",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "PHASE_REJECTED",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "PHASE_REQUEST",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "PHASE_TRANSACTION",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "TOTAL_PHASES",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"},
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
        ],
        "name": "canSign",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
        "name": "claimBudget",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "provider", "type": "address"},
            {"internalType": "address", "name": "evaluator", "type": "address"},
            {"internalType": "uint256", "name": "expiredAt", "type": "uint256"},
        ],
        "name": "createJob",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"internalType": "string", "name": "content", "type": "string"},
            {
                "internalType": "enum InteractionLedger.MemoType",
                "name": "memoType",
                "type": "uint8",
            },
            {"internalType": "bool", "name": "isSecured", "type": "bool"},
            {"internalType": "uint8", "name": "nextPhase", "type": "uint8"},
        ],
        "name": "createMemo",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "evaluatorFeeBP",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"internalType": "uint256", "name": "offset", "type": "uint256"},
            {"internalType": "uint256", "name": "limit", "type": "uint256"},
        ],
        "name": "getAllMemos",
        "outputs": [
            {
                "components": [
                    {"internalType": "string", "name": "content", "type": "string"},
                    {
                        "internalType": "enum InteractionLedger.MemoType",
                        "name": "memoType",
                        "type": "uint8",
                    },
                    {"internalType": "bool", "name": "isSecured", "type": "bool"},
                    {"internalType": "uint8", "name": "nextPhase", "type": "uint8"},
                    {"internalType": "uint256", "name": "jobId", "type": "uint256"},
                    {"internalType": "address", "name": "sender", "type": "address"},
                ],
                "internalType": "struct InteractionLedger.Memo[]",
                "name": "",
                "type": "tuple[]",
            },
            {"internalType": "uint256", "name": "total", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"internalType": "uint8", "name": "phase", "type": "uint8"},
            {"internalType": "uint256", "name": "offset", "type": "uint256"},
            {"internalType": "uint256", "name": "limit", "type": "uint256"},
        ],
        "name": "getMemosForPhase",
        "outputs": [
            {
                "components": [
                    {"internalType": "string", "name": "content", "type": "string"},
                    {
                        "internalType": "enum InteractionLedger.MemoType",
                        "name": "memoType",
                        "type": "uint8",
                    },
                    {"internalType": "bool", "name": "isSecured", "type": "bool"},
                    {"internalType": "uint8", "name": "nextPhase", "type": "uint8"},
                    {"internalType": "uint256", "name": "jobId", "type": "uint256"},
                    {"internalType": "address", "name": "sender", "type": "address"},
                ],
                "internalType": "struct InteractionLedger.Memo[]",
                "name": "",
                "type": "tuple[]",
            },
            {"internalType": "uint256", "name": "total", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getPhases",
        "outputs": [{"internalType": "string[6]", "name": "", "type": "string[6]"}],
        "stateMutability": "pure",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "role", "type": "bytes32"}],
        "name": "getRoleAdmin",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"internalType": "address", "name": "account", "type": "address"},
        ],
        "name": "grantRole",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"internalType": "address", "name": "account", "type": "address"},
        ],
        "name": "hasRole",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "paymentTokenAddress", "type": "address"},
            {"internalType": "uint256", "name": "evaluatorFeeBP_", "type": "uint256"},
            {"internalType": "uint256", "name": "platformFeeBP_", "type": "uint256"},
            {"internalType": "address", "name": "platformTreasury_", "type": "address"},
        ],
        "name": "initialize",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"internalType": "address", "name": "account", "type": "address"},
        ],
        "name": "isJobEvaluator",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "jobCounter",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"internalType": "uint8", "name": "phase", "type": "uint8"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "name": "jobMemoIds",
        "outputs": [{"internalType": "uint256", "name": "memoIds", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "jobs",
        "outputs": [
            {"internalType": "uint256", "name": "id", "type": "uint256"},
            {"internalType": "address", "name": "client", "type": "address"},
            {"internalType": "address", "name": "provider", "type": "address"},
            {"internalType": "uint256", "name": "budget", "type": "uint256"},
            {"internalType": "uint256", "name": "amountClaimed", "type": "uint256"},
            {"internalType": "uint8", "name": "phase", "type": "uint8"},
            {"internalType": "uint256", "name": "memoCount", "type": "uint256"},
            {"internalType": "uint256", "name": "expiredAt", "type": "uint256"},
            {"internalType": "address", "name": "evaluator", "type": "address"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "memoCounter",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "numEvaluatorsPerJob",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "paymentToken",
        "outputs": [{"internalType": "contract IERC20", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "platformFeeBP",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "platformTreasury",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"internalType": "address", "name": "callerConfirmation", "type": "address"},
        ],
        "name": "renounceRole",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"internalType": "address", "name": "account", "type": "address"},
        ],
        "name": "revokeRole",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "setBudget",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "memoId", "type": "uint256"},
            {"internalType": "bool", "name": "isApproved", "type": "bool"},
            {"internalType": "string", "name": "reason", "type": "string"},
        ],
        "name": "signMemo",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "memoId", "type": "uint256"},
            {"internalType": "address", "name": "signer", "type": "address"},
        ],
        "name": "signatories",
        "outputs": [{"internalType": "uint8", "name": "res", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes4", "name": "interfaceId", "type": "bytes4"}],
        "name": "supportsInterface",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "evaluatorFeeBP_", "type": "uint256"},
        ],
        "name": "updateEvaluatorFee",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "platformFeeBP_", "type": "uint256"},
            {"internalType": "address", "name": "platformTreasury_", "type": "address"},
        ],
        "name": "updatePlatformFee",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]
