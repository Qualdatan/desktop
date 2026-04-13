<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<script lang="ts">
  import 'bootstrap/dist/css/bootstrap.min.css';
  import 'bootstrap-icons/font/bootstrap-icons.css';
  import {
    Navbar,
    NavbarBrand,
    Nav,
    NavItem,
    NavLink,
    Container
  } from '@sveltestrap/sveltestrap';

  let { children } = $props();
</script>

<Navbar color="dark" dark expand="md" class="px-3">
  <NavbarBrand href="/">
    <i class="bi bi-diagram-3-fill me-2"></i>Qualdatan
  </NavbarBrand>
  <Nav navbar>
    <NavItem>
      <NavLink href="/">Projekte</NavLink>
    </NavItem>
    <NavItem>
      <NavLink href="/plugins">Plugins</NavLink>
    </NavItem>
    <NavItem>
      <NavLink href="/settings">Einstellungen</NavLink>
    </NavItem>
  </Nav>
</Navbar>

<Container fluid class="py-3">
  {@render children?.()}
</Container>
