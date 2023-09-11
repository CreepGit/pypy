# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


from typing import Optional


class Solution:
    def addTwoNumbers(self, l1, l2):
        """
        :type l1: ListNode
        :type l2: ListNode
        """
        number1 = ""
        nxt = l1
        while nxt:
            number1 += str(nxt.val)
            nxt = nxt.next

        number2 = ""
        nxt = l2
        while nxt:
            number2 += str(nxt.val)
            nxt = nxt.next

        number3 = int(number1[::-1]) + int(number2[::-1])

        nxt = None
        for c in str(number3)[::]:
            nxt = ListNode(int(c), nxt)
        return nxt
