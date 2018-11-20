---
title: "leetcode: Median of Two Sorted Arrays"
date: 2018-11-13T10:30:00+08:00
toc: true

categories:
- "programming basic"

tags:
- "git"

---


# 题目

> 
Median of Two Sorted Arrays
There are two sorted arrays nums1 and nums2 of size m and n respectively.
Find the median of the two sorted arrays. The overall run time complexity should be O(log (m+n)).
You may assume nums1 and nums2 cannot be both empty.
Example 1:
nums1 = [1, 3]
nums2 = [2]
The median is 2.0
Example 2:
nums1 = [1, 2]
nums2 = [3, 4]
The median is (2 + 3)/2 = 2.5

# 主要思想

为找到合适的位置划分两个数组:

在nums1和nums2两个数组中分别截取i,j两个长度，将两个数组划分成4部分，使

- 划分后两个数组的左部分的数量和与右部分数量和相等 i+j == (m+n)/2 (奇数偶数情况都满足此式）   &&
- 左部分的最大值小于右部分的最小值 max(nums1[i-1], nums2[j-1]) <  min(nums1[i], nums2[j]) (由于数组有序)

注： i==0时，nums所有元素被分配到右方； i==nums1.length时，nums所有元素被分到左方

则:

- 当m+n为偶数时，(max(nums1[i-1], nums1[j-1]) + min(nums1[i], nums2[j]))/2对应的位置为中位数的位置
- 当m+n为奇数时，max(nums1[i-1], nums1[j-1])对应的位置为中位数的位置

# 具体实现

在nums1中二分查找i，对于每个i可以直接计算 j=(m+n)/2-i，然后判断是否满足条件，不满足条件则继续搜索。 

主要的麻烦在于处理几个极端情况，i、j为0和长度为最大时。

leetcode题目的解决方案提到需要让i成为较长的数组，上面的处理没用到。

此时算法复杂度为O(log(m))，将数组调换位置，每次搜索较短的数组，能够将算法复杂度降低到O**(log(min(m,n)))。

```java
class Solution {
    public double findMedianSortedArrays(int[] nums1, int[] nums2) {
        if (nums1.length == 0)
            return (nums2[(nums2.length - 1) / 2] + nums2[nums2.length / 2]) / 2.0;
        if (nums2.length == 0) // return median of nums1
            return (nums1[(nums1.length - 1) / 2] + nums1[nums1.length / 2]) / 2.0;

        int iMin = 0;
        int iMax = nums1.length;
        int i;  // represent begin of right array of divided position, range in [0, nums1.length]
        // i = 0 means all nums1 will be put in right
        // i = nums1.length means all nums1 will be put in left

        while (iMin <= iMax) {
            i = (iMin + iMax) / 2;

            int j = (nums1.length + nums2.length) / 2 - i;  // range in [0, jNum.length]
            if (j < 0) {
                iMax = i - 1;
                continue;
            } else if (j > nums2.length) {
                iMin = i + 1;
                continue;
            }

            int leftEnd1; // end element of left part in nums1
            int leftEnd2;
            int rightBegin1;
            int rightBegin2;

            //  nums1 may be all put to right(==0) or left(==nums1.length)
            if (i == 0) {
                leftEnd1 = Integer.MIN_VALUE; // leftEnd1 is not existed
                rightBegin1 = nums1[i];
            } else if (i == nums1.length) {
                leftEnd1 = nums1[i - 1];
                rightBegin1 = Integer.MAX_VALUE;
            } else {
                leftEnd1 = nums1[i - 1];
                rightBegin1 = nums1[i];
            }

            //  nums2 may be all put to right(==0) or left(==nums2.length)
            if (j == 0) {
                leftEnd2 = Integer.MIN_VALUE;
                rightBegin2 = nums2[j];
            } else if (j == nums2.length) {
                leftEnd2 = nums2[j - 1];
                rightBegin2 = Integer.MAX_VALUE;
            } else {
                leftEnd2 = nums2[j - 1];
                rightBegin2 = nums2[j];
            }

            int maxLeftEnd = Math.max(leftEnd1, leftEnd2);
            int minRightBegin = Math.min(rightBegin1, rightBegin2);

            if (maxLeftEnd <= minRightBegin) {
                if ((nums1.length + nums2.length) % 2 == 0)
                    return (minRightBegin + maxLeftEnd) / 2.0;
                else
                    return minRightBegin;
            } else {
                if (j == 0)
                    iMax = i - 1;
                else if (i == 0)
                    iMin = i + 1;
                else if (nums1[i - 1] > nums2[j - 1])
                    iMax = i - 1;
                else
                    iMin = i + 1;
            }
        }

        return -999;
    }
}

public class _4MedianOfTwoSortedArrays {

    public static void main(String[] argv) {
        int[] nums1 = {1, 3, 4};
        int[] nums2 = {2, 5, 8, 10};

        Solution solution = new Solution();
        double result = solution.findMedianSortedArrays(nums1, nums2);
        System.out.println(result);
    }
}
```



