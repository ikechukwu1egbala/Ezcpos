import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  int _currentIndex = 0;

  final List<String> _titles = [
    'Dashboard',
    'Sales',
    'Products',
    'Inventory',
    'Customers',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_currentIndex]),
        actions: [
          IconButton(
            tooltip: 'Notifications',
            onPressed: () {},
            icon: const Icon(Icons.notifications_none),
          ),
          PopupMenuButton<String>(
            onSelected: (value) {},
            itemBuilder: (context) => const [
              PopupMenuItem(
                value: 'profile',
                child: Text('Profile'),
              ),
              PopupMenuItem(
                value: 'settings',
                child: Text('Settings'),
              ),
              PopupMenuItem(
                value: 'logout',
                child: Text('Logout'),
              ),
            ],
          ),
        ],
      ),

      body: _buildCurrentPage(),

      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.point_of_sale_outlined),
            selectedIcon: Icon(Icons.point_of_sale),
            label: 'Sales',
          ),
          NavigationDestination(
            icon: Icon(Icons.inventory_2_outlined),
            selectedIcon: Icon(Icons.inventory_2),
            label: 'Products',
          ),
          NavigationDestination(
            icon: Icon(Icons.warehouse_outlined),
            selectedIcon: Icon(Icons.warehouse),
            label: 'Inventory',
          ),
          NavigationDestination(
            icon: Icon(Icons.people_outline),
            selectedIcon: Icon(Icons.people),
            label: 'Customers',
          ),
        ],
      ),
    );
  }

  Widget _buildCurrentPage() {
    switch (_currentIndex) {
      case 0:
        return _dashboard();

      case 1:
        return const Center(
          child: Text('Sales'),
        );

      case 2:
        return const Center(
          child: Text('Products'),
        );

      case 3:
        return const Center(
          child: Text('Inventory'),
        );

      case 4:
        return const Center(
          child: Text('Customers'),
        );

      default:
        return _dashboard();
    }
  }

  Widget _dashboard() {
    return RefreshIndicator(
      onRefresh: () async {},
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Good morning 👋',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: AppTheme.ezcDarkBrown,
            ),
          ),

          const SizedBox(height: 4),

          const Text(
            'Here is your business overview.',
            style: TextStyle(
              color: Colors.black54,
            ),
          ),

          const SizedBox(height: 20),

          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 8,
            mainAxisSpacing: 8,
            childAspectRatio: 1.25,
            children: const [
              _StatCard(
                title: "Today's Sales",
                value: '₦0.00',
                icon: Icons.trending_up,
              ),
              _StatCard(
                title: 'Transactions',
                value: '0',
                icon: Icons.receipt_long,
              ),
              _StatCard(
                title: 'Products',
                value: '0',
                icon: Icons.inventory_2,
              ),
              _StatCard(
                title: 'Low Stock',
                value: '0',
                icon: Icons.warning_amber,
              ),
            ],
          ),

          const SizedBox(height: 24),

          const Text(
            'Quick actions',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),

          const SizedBox(height: 12),

          Row(
            children: [
              Expanded(
                child: _QuickAction(
                  icon: Icons.add_shopping_cart,
                  label: 'New Sale',
                  onTap: () {},
                ),
              ),
              Expanded(
                child: _QuickAction(
                  icon: Icons.add_box_outlined,
                  label: 'Add Product',
                  onTap: () {},
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          Row(
            children: [
              Expanded(
                child: _QuickAction(
                  icon: Icons.person_add_alt_1,
                  label: 'Customer',
                  onTap: () {},
                ),
              ),
              Expanded(
                child: _QuickAction(
                  icon: Icons.bar_chart,
                  label: 'Reports',
                  onTap: () {},
                ),
              ),
            ],
          ),

          const SizedBox(height: 24),

          Card(
            child: ListTile(
              leading: const CircleAvatar(
                backgroundColor: AppTheme.ezcLightBrown,
                child: const Icon(
                  Icons.cloud_done,
                  color: AppTheme.ezcBrown,
                ),
              ),
              title: const Text('Sync status'),
              subtitle: const Text(
                'Ready to connect to EZC server',
              ),
              trailing: const Icon(
                Icons.check_circle,
                color: Colors.green,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;

  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              color: AppTheme.ezcBrown,
              size: 28,
            ),
            const SizedBox(height: 8),
            Text(
              title,
              style: const TextStyle(
                fontSize: 13,
                color: Colors.black54,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _QuickAction({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(
            vertical: 18,
            horizontal: 8,
          ),
          child: Column(
            children: [
              Icon(
                icon,
                size: 30,
                color: AppTheme.ezcBrown,
              ),
              const SizedBox(height: 8),
              Text(
                label,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
