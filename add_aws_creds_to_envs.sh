#!/bin/bash
echo Enter AWS Access Key ID: 
read AWS_ACCESS
echo Enter AWS Secret Access Key: 
read AWS_SECRET
for i in {1..26}
do
  echo "AWS_ACCESS_KEY=$AWS_ACCESS" >> "env_files/client${i}.env"
  echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET" >> "env_files/client${i}.env"
done
