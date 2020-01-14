# Use latest arch base
FROM archlinux/base:latest

# Generate mirrorlist
ARG MIRRORLIST_COUNTRY=GB
COPY ./image/rankmirrors /usr/local/bin/rankmirrors
RUN curl -s "https://www.archlinux.org/mirrorlist/?country=$MIRRORLIST_COUNTRY&protocol=https&use_mirror_status=on" \
    | sed -e 's/^#Server/Server/' -e '/^#/d' \
    | rankmirrors -n 5 - > /etc/pacman.d/mirrorlist

# Set pacman color output
RUN sed -i "s/#Color/Color/" /etc/pacman.conf

# Init pacman and install base dev packages
RUN pacman-key --init && \
    pacman -Syyu --noconfirm && \
    pacman -S --noconfirm --needed base-devel

# Optimise packager
RUN sed -i "s/PKGEXT=.*/PKGEXT='.pkg.tar'/" /etc/makepkg.conf && \
    sed -i "s/#MAKEFLAGS=.*/MAKEFLAGS=\"-j\$(( \$(nproc) + 1 ))\"/" /etc/makepkg.conf

# Install yay
RUN mkdir /tmp/yay && \
    cd /tmp/yay && \
    curl -s https://api.github.com/repos/Jguer/yay/releases/latest | \
    grep "browser_download_url.*x86_64.tar.gz" | \
    cut -d : -f 2,3 | \
    tr -d '"' | \
    xargs curl -JL | \
    tar xfz - && \
    mv yay*/yay /usr/local/bin/yay && \
    cd / && \
    rm -r /tmp/yay

# Add build user with sudo rights
RUN useradd -ms /bin/bash builduser && \
    echo "builduser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/builduser

# Set user to build user
USER builduser

# Download test packages but don't install
RUN yay -S --downloadonly --noconfirm namcap shellcheck-static

# Copy package files
COPY --chown=builduser image/shellcheck_stub.sh packages/shellcheck_stub.sh
COPY --chown=builduser image/test.sh packages/test.sh
COPY --chown=builduser packages /packages
