ip="13.52.178.187"
echo "removing old release..."
rm e3-release.zip 2&> /dev/null
ssh -i ~/.ssh/11222024.pem ubuntu@$ip "sudo rm /opt/e3-release.zip 2&> /dev/null"
ssh -i ~/.ssh/11222024.pem ubuntu@$ip "sudo rm -rf /opt/e3 2&> /dev/null"
echo "Creating new release..."
git archive -o e3-release.zip HEAD
echo "Deploying new release..."
scp -r -i ~/.ssh/11222024.pem e3-release.zip ubuntu@$ip:/home/ubuntu/
ssh -i ~/.ssh/11222024.pem ubuntu@$ip "sudo mv /home/ubuntu/e3-release.zip /opt/"
ssh -i ~/.ssh/11222024.pem ubuntu@$ip "cd /opt;mkdir -p /opt/e3;sudo unzip /opt/e3-release.zip -d /opt/e3"

# ssh -i ~/.ssh/11222024.pem ubuntu@$ip "ls"

# scp -r -i ~/.ssh/11222024.pem migueltillisjr.com/ ubuntu@$ip:/home/ubuntu/

#   ssh -i ~/.ssh/11222024.pem ubuntu@$ip \
#   "sudo mv /home/ubuntu/migueltillisjr.com/* /var/www/html/"


# ssh -i ~/.ssh/11222024.pem 54.183.247.192