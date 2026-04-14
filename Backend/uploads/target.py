'''
-> Naive Approach:- O(nk) and O(1)
-> Better Approach: - O(nlogk) and O(logk)
'''

from typing import Optional
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def mergeKLists(self, lists: list[Optional[ListNode]]) -> Optional[ListNode]:
        ind = len(lists)
        i = 0
        while i < ind:
            dummy = ListNode(0)
            l1 = lists[i]
            l2 = lists[i+1] if i+1 < len(lists) else None
            dummy.next = self.merge_lists(l1,l2)
            lists.append(dummy.next)
            ind += 1
            i += 2

        if lists:
            return lists[-1]
        else:
            return None

    def merge_lists(self,l1,l2):
        res = ListNode(0)
        node = res

        while l1 and l2:
            if l1.val <= l2.val:
                node.next = l1
                l1 = l1.next
            else:
                node.next = l2
                l2 = l2.next
            node = node.next

        node.next = l1 if l1 else l2

        return res.next

def create_linked_list(values):
    """Create a linked list from a list of values."""
    if not values:
        return None
    head = ListNode(values[0])
    current = head
    for val in values[1:]:
        current.next = ListNode(val)
        current = current.next
    return head

def print_linked_list(head):
    """Print values of linked list."""
    current = head
    while current:
        print(current.val, end=" -> " if current.next else " -> None\n")
        current = current.next

# # Example usage and testing
# if __name__ == "__main__":
#     solution = Solution()
#
#     # Example lists to merge
#     list1 = create_linked_list([])
#     list2 = create_linked_list([-1,5,11])
#     list3 = create_linked_list([])
#     list4 = create_linked_list([6,10])
#
#     merged_list = solution.mergeKLists([list1,list2,list3,list4])
#
#     print("Merged List:")
#     print_linked_list(merged_list)