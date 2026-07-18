// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title OracleVerifier
 * @dev Benchmark contract for ECDSA, BLS, and PQC Oracle price feed updates.
 */
contract OracleVerifier {
    
    struct PriceUpdate {
        bytes32 feedId;
        uint256 price;
        uint256 timestamp;
    }

    mapping(bytes32 => uint256) public latestPrices;
    mapping(bytes32 => uint256) public latestTimestamps;

    event PriceUpdated(bytes32 indexed feedId, uint256 price, uint256 timestamp);

    /**
     * @notice Classical ECDSA price update (Individual verification via ecrecover)
     */
    function updatePriceECDSA(
        bytes32 feedId,
        uint256 price,
        uint256 timestamp,
        bytes[] calldata signatures,
        address[] calldata signers
    ) external returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(feedId, price, timestamp));
        bytes32 ethSignedMessageHash = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", messageHash)
        );

        uint256 validSignatures = 0;
        for (uint256 i = 0; i < signatures.length; i++) {
            bytes memory sig = signatures[i];
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

        require(validSignatures >= (signatures.length * 2) / 3 + 1, "Insufficient valid signatures");
        latestPrices[feedId] = price;
        latestTimestamps[feedId] = timestamp;

        emit PriceUpdated(feedId, price, timestamp);
        return true;
    }

    /**
     * @notice Emulated Precompile PQC / Aggregated price update
     */
    function updatePricePQC(
        bytes32 feedId,
        uint256 price,
        uint256 timestamp,
        bytes calldata aggregatePayload,
        uint256 verificationGasCost
    ) external returns (bool) {
        // Simulates EVM precompile execution for PQC / Batch verification
        // Calldata gas is automatically paid; verification gas is consumed via dummy workload
        uint256 startGas = gasleft();
        while (startGas - gasleft() < verificationGasCost) {
            // Burn simulated precompile gas cost
        }

        latestPrices[feedId] = price;
        latestTimestamps[feedId] = timestamp;

        emit PriceUpdated(feedId, price, timestamp);
        return true;
    }
}
