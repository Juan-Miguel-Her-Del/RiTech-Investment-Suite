import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../auth/session.dart';

final quoteProvider = FutureProvider.autoDispose<Map<String, dynamic>>((
  ref,
) async {
  final session = ref.watch(sessionProvider).asData?.value;
  if (session == null) throw const ApiException('Inicia sesión.');
  final controller = ref.read(sessionProvider.notifier);
  try {
    return await ref
        .read(apiClientProvider)
        .request('/quotes/nasdaq100', token: session.token);
  } on ApiException catch (error) {
    if (error.statusCode == 401 && ref.mounted)
      controller.expireIfCurrent(session.token);
    rethrow;
  }
});

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key, required this.session});
  final Session session;
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final quote = ref.watch(quoteProvider);
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('RiTech · Dashboard'),
        actions: [
          IconButton(
            tooltip: 'Cerrar sesión',
            onPressed: () => ref.read(sessionProvider.notifier).logout(),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Text('Hola, ${session.name}', style: theme.textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text(session.role, style: theme.textTheme.titleMedium),
            const SizedBox(height: 32),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Expanded(child: Text('NASDAQ 100')),
                        IconButton(
                          tooltip: 'Actualizar cotización',
                          onPressed: quote.isLoading
                              ? null
                              : () => ref.invalidate(quoteProvider),
                          icon: const Icon(Icons.refresh),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    quote.when(
                      loading: () =>
                          const Center(child: CircularProgressIndicator()),
                      error: (error, _) => Text(
                        error is ApiException
                            ? error.message
                            : 'No se pudo consultar la cotización.',
                      ),
                      data: (data) {
                        final value = num.tryParse('${data['value']}');
                        final updated = DateTime.tryParse(
                          '${data['updated_at']}',
                        );
                        if (value == null || !value.isFinite || updated == null)
                          return const Text(
                            'La cotización recibida no es válida.',
                          );
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${value.toStringAsFixed(2)} pts',
                              style: theme.textTheme.headlineMedium,
                            ),
                            const SizedBox(height: 8),
                            Text('Actualizado: ${updated.toLocal()}'),
                            const SizedBox(height: 12),
                            if (data['is_demo'] == true)
                              const Chip(
                                avatar: Icon(Icons.science_outlined),
                                label: Text('Datos simulados de desarrollo'),
                              ),
                          ],
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
