pragma solidity ^0.8.13;

contract Counter {
    uint public count;
    address public owner;

    function multiTransfer(address payable[] memory recipients) payable public returns (address) {
        // msg.value
        // address payable[] memory recipients = new address payable[](5);
        // recipients[0] = payable(address(0x11B5B9b4083DC3C0960Da1C1d89DBbDeeC42Bc50));
        // recipients[1] = payable(address(0x14A5Ab64E913e8B3116247A58Ac99c1830f97E4a));
        // recipients[2] = payable(address(0x124A68bE86aF40d6e39C63B4F025055c3c39B510));
        // recipients[3] = payable(address(0x1C16c75B915068a8C76DF522bA9A659A47d1F245));
        // recipients[4] = payable(address(0x13bDB54886d9f03FAC52609Cbf40F60b088D806e));
        
        uint256 amount = 0.001 ether;

        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), "Invalid recipient address");
            recipients[i].transfer(amount);
        }
        return recipients[0];
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