# Maintainer: Your Name <you@example.com>
pkgname=freedomnas-module-example
pkgver=1.0.0
pkgrel=1
pkgdesc="Example FreedomNAS community module"
arch=('any')
url="https://codeberg.org/you/freedomnas-module-example"
license=('MPL-2.0')
depends=('freedomnas-core' 'freedomnas-webui')
source=("git+https://codeberg.org/you/freedomnas-module-example.git#tag=v${pkgver}")
sha256sums=('SKIP')

package() {
    cd "${srcdir}/${pkgname}"

    mkdir -p "${pkgdir}/usr/lib/freedomnas/modules"
    mkdir -p "${pkgdir}/usr/lib/freedomnas/profiles"
    cp -r modules/example  "${pkgdir}/usr/lib/freedomnas/modules/example"
    cp -r profiles/example "${pkgdir}/usr/lib/freedomnas/profiles/example"

    # Drop the *.example placeholders — rename them before building your
    # real module (see README.md "Adding a WebUI page").
    find "${pkgdir}/usr/lib/freedomnas/modules/example" -name '*.example' -delete

    [ -f LICENSE ] && install -Dm 644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
    [ -f README.md ] && install -Dm 644 README.md "${pkgdir}/usr/share/doc/${pkgname}/README.md"
}
