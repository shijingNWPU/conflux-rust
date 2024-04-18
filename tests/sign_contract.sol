pragma solidity ^0.8.13;

contract Counter {
    uint public count;
    address public owner;

    function multiTransfer() payable public {
        // msg.value
        address payable[] memory recipients = new address payable[](2);
        recipients[0] = payable(address(0x11B5B9b4083DC3C0960Da1C1d89DBbDeeC42Bc50));
        recipients[1] = payable(address(0x14A5Ab64E913e8B3116247A58Ac99c1830f97E4a));
        uint256 amount = 0.001 ether;

        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), "Invalid recipient address");
            recipients[i].transfer(amount);
        }
    }

    event Change(address indexed sender, uint new_value);

    constructor(uint init_value) {
        count = init_value;
        owner = msg.sender;
    }

    // Function to get the current count
    function get() public view returns (uint) {
        return count;
    }

    // Function to increment count by 1
    function inc() public {
        count += 1;
        emit Change(msg.sender, count);
    }
}