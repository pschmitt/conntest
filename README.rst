conntest
============

This library helps you check credentials.

It support the following protocols:

- RDP
- SSH
- VNC
- VMware vCenter Auth

Usage
-----------

.. code ::

    import conntest
    conntest.ssh_connection(
        '127.0.0.1', username='root', password='something', port=22
    )
    conntest.rdp_connection(
        '127.0.0.1', port=3389, username='Administrator',
        domain='example.com', password='something'
    )
    conntest.vnc_connection(
        '127.0.0.1', port=5900, password='something'
    )
    conntest.vcenter_connection(
        '127.0.0.1', port=443, username='administrator',
        domain='vsphere.local', password='something'
    )

