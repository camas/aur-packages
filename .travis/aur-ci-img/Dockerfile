# Arch base
FROM archlinux/base:latest

# Add build user with sudo rights
RUN useradd -ms /bin/bash builduser
RUN echo "builduser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/builduser

# Init pacman and install git/yay
COPY mirrorlist /etc/pacman.d/mirrorlist
RUN pacman-key --init && \
    pacman -Syyu --noconfirm && \
    pacman -S --noconfirm base-devel && \
    pacman -S --noconfirm git && \
    git clone https://aur.archlinux.org/yay.git && \
    cd yay && \
    makepkg -si && \
    cd ../ && \
    rm -rf yay

USER builduser
