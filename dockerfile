FROM centos:7

# changing the old repo to the new functional one
RUN sed -i 's|mirrorlist=|#mirrorlist=|g' /etc/yum.repos.d/CentOS-*.repo && \
    sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*.repo 

# instll ssh and python
RUN yum install -y openssh-server python3 python3-pip && \
    yum clean all

RUN pip3 install twisted 
# config ssh
RUN ssh-keygen -A && \
    echo "root:vulcanet" | chpasswd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
    # allow login as root

EXPOSE 22 5678

CMD ["/usr/sbin/sshd", "-D"]