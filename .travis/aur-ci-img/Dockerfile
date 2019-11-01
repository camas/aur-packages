# Use latest arch base
FROM archlinux/base:latest

COPY ./.travis/rankmirrors /usr/local/bin/rankmirrors
RUN curl -s "https://www.archlinux.org/mirrorlist/?country=US&protocol=https&use_mirror_status=on" \
    | sed -e 's/^#Server/Server/' -e '/^#/d' \
    | rankmirrors -n 5 - > /etc/pacman.d/mirrorlist

# Init pacman and install base dev packages
RUN pacman-key --init && \
    pacman -Syyu --noconfirm && \
    pacman -S --noconfirm --needed base-devel

# Install yay
RUN curl -s https://api.github.com/repos/Jguer/yay/releases/latest | \
    grep "browser_download_url.*x86_64.tar.gz" | \
    cut -d : -f 2,3 | \
    tr -d '"' | \
    xargs curl -JL | \
    tar xfz - && \
    mv yay*/yay /usr/local/bin/yay && \
    rm -rf yay*

# Add build user with sudo rights
RUN useradd -ms /bin/bash builduser && \
    echo "builduser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/builduser

# Set user to build user
USER builduser

# Install packages needed to run the packager
RUN yay -Syu --noconfirm && \
    yay -S --noconfirm --needed python-clicolor git namcap
