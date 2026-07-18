// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title OracleVerifier
 * @dev Secure benchmark contract for ECDSA, BLS, and PQC Oracle price feed updates.
 */
contract OracleVerifier {
    
    address public owner;
    mapping(address => bool) public authorizedNodes;

    mapping(bytes32 => uint256) public latestPrices;
    mapping(bytes32 => uint256) public latestTimestamps;

    event PriceUpdated(bytes32 indexed feedId, uint256 price, uint256 timestamp);
    event NodeAuthorizationChanged(address indexed node, bool authorized);

    modifier onlyOwner() {
        require(msg.sender == owner, "OracleVerifier: caller is not owner");
        _;
    }

    modifier onlyAuthorized() {
        require(authorizedNodes[msg.sender] || msg.sender == owner, "OracleVerifier: caller is not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedNodes[msg.sender] = true;
    }

    function setNodeAuthorization(address node, bool authorized) external onlyOwner {
        authorizedNodes[node] = authorized;
        emit NodeAuthorizationChanged(node, authorized);
    }

    /**
     * @notice Classical ECDSA price update (Individual verification via ecrecover)
     */
    function updatePriceECDSA(
        bytes32 feedId,
        uint256 price,
        uint256 timestamp,
        bytes[] calldata signatures,
        address[] calldata signers
    ) external onlyAuthorized returns (bool) {
        require(signatures.length == signers.length, "OracleVerifier: length mismatch");
        require(signatures.length > 0, "OracleVerifier: empty signatures");

        bytes32 messageHash = keccak256(abi.encodePacked(feedId, price, timestamp));
        bytes32 ethSignedMessageHash = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", messageHash)
        );

        uint256 validSignatures = 0;
        for (uint256 i = 0; i < signatures.length; i++) {
            bytes memory sig = signatures[i];
            require(sig.length == 65, "OracleVerifier: invalid sig length");

            bytes32 r;
            bytes32 s;
            uint8 v;
            assembly {
                r := mload(add(sig, 32))
                s := mload(add(sig, 64))
                v := byte(0, mload(add(sig, 96)))
            }
            address recovered = ecrecover(ethSignedMessageHash, v, r, s);
            if (recovered == signers[i] && recovered != address(0)) {
                validSignatures++;
            }
        }

        uint256 threshold = (signatures.length * 2) / 3 + 1;
        require(validSignatures >= threshold, "OracleVerifier: insufficient valid signatures");

        // Checks-Effects-Interactions pattern
        latestPrices[feedId] = price;
        latestTimestamps[feedId] = timestamp;

        emit PriceUpdated(feedId, price, timestamp);
        return true;
    }

    /**
     * @notice PQC / Aggregated price update precompile interface
     */
    function updatePricePQC(
        bytes32 feedId,
        uint256 price,
        uint256 timestamp,
        bytes calldata aggregatePayload,
        address precompileAddress
    ) external onlyAuthorized returns (bool) {
        require(aggregatePayload.length > 0, "OracleVerifier: empty payload");
        require(timestamp <= block.timestamp + 300, "OracleVerifier: timestamp in future");

        // Execute static call to PQC verification precompile if precompileAddress is provided
        if (precompileAddress != address(0)) {
            (bool success, bytes memory result) = precompileAddress.staticcall(
                abi.encode(feedId, price, timestamp, aggregatePayload)
            );
            require(success && result.length > 0, "OracleVerifier: precompile verification failed");
        }

        // State updates (Checks-Effects-Interactions)
        latestPrices[feedId] = price;
        latestTimestamps[feedId] = timestamp;

        emit PriceUpdated(feedId, price, timestamp);
        return true;
    }
}
