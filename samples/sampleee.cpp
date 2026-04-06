class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        int n =nums.size();
        
        unordered_map<int , int> mpp;
        for(int i=0;i<n;i++){
            mpp[nums[i]]=i;
        }

        for(int i=0;i<n;i++){
            int num = target - nums[i];
            if(mpp.find(num)!=mpp.end() && mpp[num]!=i)
            return {i ,mpp[num]};

        }
        return {-1, -1};
    }
};